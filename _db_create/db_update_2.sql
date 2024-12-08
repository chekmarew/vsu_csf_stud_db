ALTER TABLE `student`
	ADD `student_status` ENUM('study','alumnus','expelled','academic_leave') 
	COMMENT 'Состояние студента: учится, выпускник, отчислен, в академическом отпуске'
    NOT NULL DEFAULT 'study' AFTER `student_semestr`;

ALTER TABLE `stud_group` 
	ADD `stud_group_specialty` VARCHAR(200) NOT NULL COMMENT 'Специальность' AFTER `stud_group_subnum`,
	ADD `stud_group_specialization` VARCHAR(200) NULL COMMENT 'Специализация' AFTER `stud_group_specialty`;
	
ALTER TABLE `curriculum_unit` 
	ADD `mark_type_enum` ENUM('test_simple','exam','test_diff') NULL 
	COMMENT 'Тип отчётности: зачёт, экзамен, зачёт с оценкой' AFTER `mark_type`;
	
SET SQL_SAFE_UPDATES = 0;

UPDATE curriculum_unit SET mark_type_enum = 'test_simple' where mark_type = 1;
UPDATE curriculum_unit SET mark_type_enum = 'exam' where mark_type = 2;
UPDATE curriculum_unit SET mark_type_enum = 'test_diff' where mark_type = 3;
COMMIT;

ALTER TABLE `curriculum_unit` DROP `mark_type`;

ALTER TABLE `curriculum_unit` CHANGE `mark_type_enum` `mark_type` ENUM('test_simple','exam','test_diff') NOT NULL COMMENT 'Тип отчётности: зачёт, экзамен, зачёт с оценкой';