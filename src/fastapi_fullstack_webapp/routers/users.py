from typing import Annotated
from datetime import timedelta, UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, status, Query, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy import delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi.security import OAuth2PasswordRequestForm

from PIL import UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from ..image_utils import delete_profile_image, process_profile_image

from .. import models
from ..database import get_db
from ..schema import PostResponse, Token, UserCreate, UserPrivate, UserPublic, UserUpdate, PaginatedPostsResponse, ChangePasswordRequest, ForgotPasswordRequest,  ResetPasswordRequest

from ..emails_utils import send_password_reset_email
from ..auth import (
    create_access_token,
    hash_password,
    verify_access_token,
    verify_password,
    generate_reset_token,
    hash_reset_token,
    CurrentUser
)
from ..config import settings

router = APIRouter()

'''
POST /api/users
       ↓
UserCreate validation
       ↓
Check username
       ↓
Already exists? → 400
       ↓
Check email
       ↓
Already exists? → 400
       ↓
Create User ORM object
       ↓
db.add()
       ↓
db.commit()
       ↓
db.refresh()
       ↓
UserPrivate
       ↓
201 Created
'''
@router.post(
        "",
        response_model=UserPrivate,
        status_code=status.HTTP_201_CREATED
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    # Check if a user with the same username already exists
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.username) == user.username.lower(),
        ),
    )
    existing_user = result.scalars().first()

    print(f"Existing user: ", existing_user)

    # If username exists, return a 400 Bad Request error
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Check if a user with the same email already exists
    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) == user.email.lower()),
    )
    existing_email = result.scalars().first()

    # If email exists, return a 400 Bad Request error
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create a new User object
    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        password_hash=hash_password(user.password),
    )

    # Add the new user to the current database session
    db.add(new_user)

    # Save changes to the database
    await db.commit()

    # Refresh the object to get generated values (e.g., id)
    await db.refresh(new_user)

    # Return the newly created user
    return new_user

# Handle forgot password requests and send reset instructions by email
@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    # Validated request containing the user's email address
    request_data: ForgotPasswordRequest,

    # FastAPI background task manager for sending email after the response
    background_tasks: BackgroundTasks,

    # Async database session provided through dependency injection
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Search for a user with the provided email address
    result = await db.execute(
        select(models.User).where(
            # Compare emails case-insensitively
            func.lower(models.User.email) == request_data.email.lower(),
        ),
    )

    # Get the matching user or None if the email does not exist
    user = result.scalars().first()

    # Continue with reset token creation only if the user exists
    if user:
        # Delete any previous password reset tokens for this user
        # This ensures only the latest reset request remains valid
        await db.execute(
            sql_delete(models.PasswordResetToken).where(
                models.PasswordResetToken.user_id == user.id,
            ),
        )

        # Generate a secure random token that will be sent to the user
        token = generate_reset_token()

        # Hash the token before storing it in the database
        # The raw reset token is never stored in the database
        token_hash = hash_reset_token(token)

        # Calculate when the reset token should expire
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.reset_token_expire_minutes,
        )

        # Create the password reset token database record
        reset_token = models.PasswordResetToken(
            # Associate the reset token with the user
            user_id=user.id,

            # Store only the hashed version of the token
            token_hash=token_hash,

            # Store the token expiration timestamp
            expires_at=expires_at,
        )

        # Add the reset token record to the current database session
        db.add(reset_token)

        # Save the reset token in the database
        await db.commit()

        # Schedule the password reset email to be sent in the background
        # This allows the API response to return without waiting for SMTP
        background_tasks.add_task(
            send_password_reset_email,

            # Send the email to the user's registered email address
            to_email=user.email,

            # Pass username so the email can be personalized
            username=user.username,

            # Send the raw token so it can be included in the reset URL
            token=token,
        )

    # Always return the same response whether or not the email exists
    # This prevents attackers from discovering registered email addresses
    return {
        "message": "If an account exists with this email, you will receive password reset instructions.",
    }

# Reset the user's password using a valid password reset token
@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    # Request contains the reset token and new password
    request_data: ResetPasswordRequest,

    # Async database session
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Hash the raw token received from the reset password request
    # This allows comparison with the hashed token stored in the database
    token_hash = hash_reset_token(request_data.token)

    # Search for the password reset token in the database
    result = await db.execute(
        select(models.PasswordResetToken).where(
            # Compare the generated hash with the stored token hash
            models.PasswordResetToken.token_hash == token_hash,
        ),
    )

    # Get the matching reset token or None
    reset_token = result.scalars().first()

    # Reject the request if the token does not exist
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check whether the reset token has expired
    if reset_token.expires_at < datetime.now(UTC):

        # Remove the expired token from the database
        await db.delete(reset_token)

        # Save the deletion
        await db.commit()

        # Reject the password reset request
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Find the user associated with the valid reset token
    result = await db.execute(
        select(models.User).where(
            models.User.id == reset_token.user_id
        ),
    )

    # Get the associated user
    user = result.scalars().first()

    # Reject the request if the associated user no longer exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Hash the new password before storing it
    user.password_hash = hash_password(request_data.new_password)

    # Delete all password reset tokens belonging to this user
    # This prevents the same token from being reused after password reset
    await db.execute(
        sql_delete(models.PasswordResetToken).where(
            models.PasswordResetToken.user_id == user.id,
        ),
    )

    # Save the new password and token deletion
    await db.commit()

    # Confirm successful password reset
    return {
        "message": "Password reset successfully. You can now log in with your new password.",
    }


# Allow an authenticated user to change their current password
@router.patch("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    # Request containing the current password and new password
    password_data: ChangePasswordRequest,

    # Currently authenticated user provided by the authentication dependency
    current_user: CurrentUser,

    # Async database session
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Verify that the provided current password matches the stored password hash
    if not verify_password(
        password_data.current_password,
        current_user.password_hash,
    ):
        # Reject the request if the current password is incorrect
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Hash the new password and replace the user's existing password hash
    current_user.password_hash = hash_password(
        password_data.new_password
    )

    # Delete any outstanding password reset tokens for this user
    # Old reset links should no longer work after the password changes
    await db.execute(
        sql_delete(models.PasswordResetToken).where(
            models.PasswordResetToken.user_id == current_user.id,
        ),
    )

    # Save the new password and reset-token deletion
    await db.commit()

    # Return confirmation to the authenticated user
    return {
        "message": "Password changed successfully"
    }

#Login Endpoint
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Look up user by email (case-insensitive)
    # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == form_data.username.lower(),
        ),
    )
    user = result.scalars().first()

    # Verify user exists and password is correct
    # Don't reveal which one failed (security best practice)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user id as subject
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")

# Me endpoint to get the current user
@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user

# Updating User
@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if (
        user_update.username is not None
        and user_update.username.lower() != user.username.lower()
    ):
        result = await db.execute(
            select(models.User).where(
                func.lower(models.User.username) == user_update.username.lower(),
            ),
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
    if (
        user_update.email is not None
        and user_update.email.lower() != user.email.lower()
    ):
        result = await db.execute(
            select(models.User).where(
                func.lower(models.User.email) == user_update.email.lower(),
            ),
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email.lower()

    await db.commit()
    await db.refresh(user)
    return user

# Deleting User
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user",
        )

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Also delete the image of the user
    old_filename = user.image_file

    await db.delete(user)
    await db.commit()
    
    # Also delete the image of the user
    if old_filename:
        delete_profile_image(old_filename)

    

# Getting specific user from database
@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


# Getting User posts route
@router.get("/{user_id}/posts", response_model=PaginatedPostsResponse)
async def get_user_posts(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = settings.posts_per_page,
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    count_result = await db.execute(
        select(func.count())
        .select_from(models.Post)
        .where(models.Post.user_id == user_id),
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
        .offset(skip)
        .limit(limit),
    )
    posts = result.scalars().all()

    has_more = skip + len(posts) < total

    return PaginatedPostsResponse(
        posts=[PostResponse.model_validate(post) for post in posts],
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )


# Upload or update the authenticated user's profile picture
@router.patch("/{user_id}/picture", response_model=UserPrivate)
async def upload_profile_picture(
    user_id: int,
    file: UploadFile,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Ensure users can only update their own profile picture
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's picture",
        )

    # Read the uploaded file into memory
    content = await file.read()

    # Validate the uploaded file size against the configured maximum limit
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is "
                   f"{settings.max_upload_size_bytes // (1024 * 1024)}MB",
        )

    try:
        # Pillow image processing is CPU-bound, so run it in a thread pool
        # to avoid blocking FastAPI's async event loop
        new_filename = await run_in_threadpool(
            process_profile_image,
            content,
        )
    except UnidentifiedImageError as err:
        # Reject files that Pillow cannot identify as valid images
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid image "
                   "(JPEG, PNG, GIF, WebP).",
        ) from err

    # Keep the old filename so it can be removed after the DB update succeeds
    old_filename = current_user.image_file

    # Store the newly generated profile picture filename in the database
    current_user.image_file = new_filename
    await db.commit()
    await db.refresh(current_user)

    # Delete the previous profile picture after the new one is successfully saved
    if old_filename:
        delete_profile_image(old_filename)

    # Return the updated authenticated user
    return current_user


# Delete the authenticated user's existing profile picture
@router.delete("/{user_id}/picture", response_model=UserPrivate)
async def delete_user_picture(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Ensure users can only delete their own profile picture
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user's picture",
        )

    # Store the current filename before removing it from the database
    old_filename = current_user.image_file

    # Return an error if the user does not currently have a profile picture
    if old_filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile picture to delete",
        )

    # Remove the profile picture reference from the user's database record
    current_user.image_file = None
    await db.commit()
    await db.refresh(current_user)

    # Delete the actual image file from storage
    delete_profile_image(old_filename)

    # Return the updated user
    return current_user