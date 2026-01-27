-- Check and create admin user
-- First, check if database exists
\c postgres
SELECT datname FROM pg_database WHERE datname='ozon_parser';

-- Connect to ozon_parser database
\c ozon_parser

-- Check if users table exists
SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='users';

-- Show all users
SELECT id, username, full_name, is_active FROM public.users;
