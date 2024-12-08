ALTER TABLE `stud_group` 
ADD COLUMN `stud_group_sub_count` TINYINT(3) UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Количество подгрупп (если student_stud_group_subnum=0)' AFTER `stud_group_subnum`;

ALTER TABLE `student` 
ADD COLUMN `student_stud_group_subnum` TINYINT(3) UNSIGNED NULL COMMENT 'Номер подгруппы' AFTER `stud_group_id`;
set sql_safe_updates=0;

update student set student_stud_group_subnum=0 where stud_group_id is not null;
commit;


ALTER TABLE `teacher` 
ADD COLUMN `teacher_right_read_all` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Право чтения всех данных';
