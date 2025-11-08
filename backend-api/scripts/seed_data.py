"""
Seed database with initial data for development and testing.

This script creates:
- A demo tenant
- An admin user
- An API key
- Rate limit configuration
"""

import asyncio
from datetime import datetime
from uuid import uuid4

from src.core.config import settings
from src.core.security import generate_api_key, get_password_hash
from src.db.models import APIKey, RateLimit, Tenant, User
from src.db.session import AsyncSessionLocal, engine


async def seed_database():
    """Seed the database with initial data."""
    print("Starting database seeding...")

    async with AsyncSessionLocal() as db:
        try:
            # Create demo tenant
            print("Creating demo tenant...")
            tenant = Tenant(
                id=uuid4(),
                name="Demo Corporation",
                slug="demo-corp",
                plan="pro",
                status="active",
                settings={
                    "default_model": "two_tower",
                    "embedding_dimension": 128,
                },
            )
            db.add(tenant)
            await db.flush()
            print(f"Created tenant: {tenant.name} (ID: {tenant.id})")

            # Create rate limit for tenant
            print("Creating rate limit configuration...")
            rate_limit = RateLimit(
                tenant_id=tenant.id,
                requests_per_minute=1000,
                requests_per_hour=50000,
                requests_per_day=1000000,
            )
            db.add(rate_limit)
            print("Rate limit configured")

            # Create admin user
            print("Creating admin user...")
            password_hash = get_password_hash("password123")
            admin_user = User(
                id=uuid4(),
                tenant_id=tenant.id,
                email="admin@demo-corp.com",
                password_hash=password_hash,
                role="admin",
                status="active",
            )
            db.add(admin_user)
            await db.flush()
            print(f"Created user: {admin_user.email} (password: password123)")

            # Create developer user
            print("Creating developer user...")
            dev_user = User(
                id=uuid4(),
                tenant_id=tenant.id,
                email="developer@demo-corp.com",
                password_hash=get_password_hash("dev123"),
                role="developer",
                status="active",
            )
            db.add(dev_user)
            print(f"Created user: {dev_user.email} (password: dev123)")

            # Create API keys
            print("Creating API keys...")

            # Production-like key
            full_key, key_hash, key_prefix = generate_api_key()
            api_key_prod = APIKey(
                id=uuid4(),
                tenant_id=tenant.id,
                name="Production Key",
                key_hash=key_hash,
                key_prefix=key_prefix,
                permissions=["read", "write"],
                status="active",
            )
            db.add(api_key_prod)
            print(f"Created API key: {api_key_prod.name}")
            print(f"  Full key (save this!): {full_key}")
            print(f"  Key prefix: {key_prefix}")

            # Test key
            full_key_test, key_hash_test, key_prefix_test = generate_api_key()
            api_key_test = APIKey(
                id=uuid4(),
                tenant_id=tenant.id,
                name="Test Key",
                key_hash=key_hash_test,
                key_prefix=key_prefix_test,
                permissions=["read"],
                status="active",
            )
            db.add(api_key_test)
            print(f"Created API key: {api_key_test.name}")
            print(f"  Full key (save this!): {full_key_test}")
            print(f"  Key prefix: {key_prefix_test}")

            # Commit transaction
            await db.commit()
            print("\n✅ Database seeding completed successfully!")

            # Print summary
            print("\n" + "=" * 60)
            print("SEED DATA SUMMARY")
            print("=" * 60)
            print(f"\nTenant: {tenant.name}")
            print(f"  ID: {tenant.id}")
            print(f"  Slug: {tenant.slug}")
            print(f"  Plan: {tenant.plan}")
            print(f"\nUsers:")
            print(f"  Admin: {admin_user.email} / password123")
            print(f"  Developer: {dev_user.email} / dev123")
            print(f"\nAPI Keys:")
            print(f"  Production: {full_key}")
            print(f"  Test: {full_key_test}")
            print(f"\nRate Limits:")
            print(f"  {rate_limit.requests_per_minute} req/min")
            print(f"  {rate_limit.requests_per_hour} req/hour")
            print(f"  {rate_limit.requests_per_day} req/day")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ Error seeding database: {e}")
            await db.rollback()
            raise


async def main():
    """Main function."""
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Environment: {settings.ENVIRONMENT}\n")

    # Wait for database to be ready
    print("Waiting for database...")
    await asyncio.sleep(2)

    # Run seeding
    await seed_database()

    # Close engine
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
