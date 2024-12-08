ALTER TABLE `lesson` 
ADD COLUMN `lesson_student_mark_active` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Включён режим отметки посещаемости студентом' AFTER `lesson_comment`;

