-- Fix nullable columns in dataset_uploads table
-- These fields aren't available at upload creation time, only after processing

ALTER TABLE dataset_uploads
    ALTER COLUMN s3_path DROP NOT NULL,
    ALTER COLUMN row_count DROP NOT NULL;

-- Update existing records if any
UPDATE dataset_uploads SET s3_path = NULL WHERE s3_path = '';
UPDATE dataset_uploads SET row_count = NULL WHERE row_count = 0;
