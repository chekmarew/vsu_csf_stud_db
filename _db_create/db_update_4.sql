ALTER TABLE `teacher` 
ADD COLUMN `teacher_active` TINYINT(1) NOT NULL DEFAULT 1 AFTER `teacher_login`;
ALTER TABLE `admin_user` 
ADD COLUMN `admin_user_active` TINYINT(1) NOT NULL DEFAULT 1;