/*
ALTER TABLE `curriculum_unit` 
CHANGE COLUMN `mark_type` `mark_type` ENUM('test_simple', 'exam', 'test_diff', 'no_mark') NOT NULL COMMENT 'Тип отчётности: зачёт, экзамен, зачёт с оценкой, нет' ;
*/

ALTER TABLE `curriculum_unit` 
ADD COLUMN `closed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Ведомость закрыта';

ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `closed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Ведомость закрыта';


set sql_safe_updates=0;
update curriculum_unit set closed=1 where curriculum_unit_status='close';
update curriculum_unit_status_hist set closed=1 where curriculum_unit_status='close';
commit;


ALTER TABLE `curriculum_unit` 
DROP COLUMN `curriculum_unit_status`;

ALTER TABLE `curriculum_unit_status_hist` 
DROP COLUMN `curriculum_unit_status`;


ALTER TABLE `att_mark`
ADD COLUMN `att_mark_comment` VARCHAR(4000) NULL COMMENT 'Комментарий для таблицы с посещаемостью';
