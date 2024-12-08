ALTER TABLE `subject` 
ADD COLUMN `subject_short_name` VARCHAR(32),
ADD UNIQUE INDEX `subject_short_name_UNIQUE` (`subject_short_name` ASC) VISIBLE;

UPDATE `subject` SET `subject_short_name` = 'Ин.яз.' WHERE `subject_id` = 2;
COMMIT;
