ALTER TABLE `stud_group` 
ADD COLUMN `lessons_start_date` DATE NULL COMMENT 'Дата начала занятий',
ADD COLUMN `session_start_date` DATE NULL COMMENT 'Дата начала экзаменационной сессии',
ADD COLUMN `session_end_date` DATE NULL COMMENT 'Дата окончания экзаменационной сессии';

ALTER TABLE `stud_group` ADD CHECK (lessons_start_date < session_start_date and session_start_date < session_end_date);