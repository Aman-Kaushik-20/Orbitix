import asyncpg
from loguru import logger
from src.utils.schemas import User

class RegisterUser:
    """Register New Users and Update in Database"""
    def __init__(self, db_pool:asyncpg.Pool) -> None:
        self.db_pool=db_pool
    
    async def register(self, user_info:User):
        try:
            async with self.db_pool.acquire() as connection:
                async with connection.transaction():
                    # Check if a user already exists with the same ID or email
                    existing_user = await connection.fetchrow(
                        "SELECT user_id FROM users WHERE user_id = $1 OR user_email = $2",
                        user_info.user_id, user_info.user_email
                    )
                    
                    if existing_user:
                        raise ValueError(f'User already exists with this ID or email.')

                    # Corrected INSERT query to include is_active (11 columns)
                    user_register_query="""
                        INSERT INTO users(
                            user_id, user_name, user_email, user_password_hash, ph_no, 
                            created_at, updated_at, last_login, is_active, 
                            timezone
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """
                    
                    # Await the execute call and pass all 11 arguments
                    await connection.execute(
                        user_register_query,
                        user_info.user_id, user_info.user_name, user_info.user_email,
                        user_info.user_password_hash, user_info.ph_no, user_info.created_at,
                        user_info.updated_at, user_info.last_login, user_info.is_active,
                        user_info.timezone
                    )
            
            logger.info(f"Successfully registered user: {user_info.user_email}")
            return "User Registered Successfully!"

        except ValueError as e:
            logger.warning(f"Registration failed for {user_info.user_email}: {e}")
            raise # Re-raise the specific error to be handled by the caller
        except Exception as e:
            logger.error(f'Something Went Wrong in User Creation Service for {user_info.user_email}: {e}')
            raise # Re-raise after logging

