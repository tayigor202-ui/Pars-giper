-- User Management System - Database Schema
-- Fine-grained permissions for OZON Parser Dashboard

CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Dashboard Permissions
    can_view_dashboard BOOLEAN DEFAULT TRUE,
    
    -- Parser Control Permissions
    can_run_parser BOOLEAN DEFAULT FALSE,
    can_view_parser_status BOOLEAN DEFAULT TRUE,
    
    -- Settings Permissions
    can_view_settings BOOLEAN DEFAULT FALSE,
    can_edit_schedules BOOLEAN DEFAULT FALSE,
    can_edit_database_settings BOOLEAN DEFAULT FALSE,
    can_import_data BOOLEAN DEFAULT FALSE,
    
    -- User Management (Admin)
    can_manage_users BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT username_length CHECK (LENGTH(username) >= 3)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON public.users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON public.users(is_active);

-- Insert default admin user (password will be hashed by init script)
-- Username: admin, Password: admin (CHANGE IN PRODUCTION!)
INSERT INTO public.users (
    username, 
    password_hash, 
    full_name, 
    is_active,
    can_view_dashboard,
    can_run_parser,
    can_view_parser_status,
    can_view_settings,
    can_edit_schedules,
    can_edit_database_settings,
    can_import_data,
    can_manage_users
) VALUES (
    'admin',
    '$2b$12$placeholder', -- Will be replaced by init script
    'Administrator',
    TRUE,
    TRUE, -- can_view_dashboard
    TRUE, -- can_run_parser  
    TRUE, -- can_view_parser_status
    TRUE, -- can_view_settings
    TRUE, -- can_edit_schedules
    TRUE, -- can_edit_database_settings
    TRUE, -- can_import_data
    TRUE  -- can_manage_users
)
ON CONFLICT (username) DO NOTHING;

COMMENT ON TABLE public.users IS 'User accounts with fine-grained permissions';
COMMENT ON COLUMN public.users.can_view_dashboard IS 'Access to dashboard page';
COMMENT ON COLUMN public.users.can_run_parser IS 'Can start parser manually';
COMMENT ON COLUMN public.users.can_view_settings IS 'Can view settings page';
COMMENT ON COLUMN public.users.can_edit_schedules IS 'Can modify parser schedules';
COMMENT ON COLUMN public.users.can_edit_database_settings IS 'Can change DB settings and import data';
COMMENT ON COLUMN public.users.can_manage_users IS 'Can create/edit/delete users (admin only)';
