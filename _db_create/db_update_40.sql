ALTER TABLE `att_mark` 
ADD COLUMN `att_mark_comment_hidden` VARCHAR(4000) NULL COMMENT 'Комментарий для таблицы с посещаемостью скрытый от студента';


ALTER TABLE `lesson` 
ADD COLUMN `lesson_comment_hidden` VARCHAR(4000) NULL COMMENT 'Комментарий для таблицы с посещаемостью скрытый от студента' AFTER `lesson_comment`,
CHANGE COLUMN `lesson_comment` `lesson_comment` VARCHAR(4000) NULL DEFAULT NULL COMMENT 'Комментарий для таблицы с посещаемостью' ;


ALTER TABLE `lesson_student` 
ADD COLUMN `lesson_student_comment_hidden` VARCHAR(4000) NULL;

