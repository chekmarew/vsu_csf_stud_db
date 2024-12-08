ALTER TABLE `att_mark` 
ADD COLUMN `simple_mark_test_simple` TINYINT(3) UNSIGNED NULL COMMENT 'Значение оценка за зачёт без аттестаций (0-неявка 2-не_зачтнено 5-зачтено)' AFTER `attendance_rate_cached`;

ALTER TABLE `att_mark` 
ADD COLUMN `simple_mark_exam` TINYINT(3) UNSIGNED NULL COMMENT 'Значение оценка за экзамен без аттестаций' AFTER `simple_mark_test_simple`;

ALTER TABLE `att_mark` 
ADD COLUMN `simple_mark_test_diff` TINYINT(3) UNSIGNED NULL COMMENT 'Значение оценка за зачёт с оценкой без аттестаций' AFTER `simple_mark_exam`;

ALTER TABLE `att_mark` 
ADD COLUMN `simple_mark_course_work` TINYINT(3) UNSIGNED NULL COMMENT 'Значение оценка за курсовую работу без аттестаций' AFTER `simple_mark_test_diff`;

ALTER TABLE `att_mark` 
ADD COLUMN `simple_mark_course_project` TINYINT(3) UNSIGNED NULL COMMENT 'Значение оценка за курсовой проект без аттестаций' AFTER `simple_mark_course_work`;


ALTER TABLE `att_mark_hist` 
ADD COLUMN `simple_mark_test_simple` TINYINT(3) UNSIGNED NULL COMMENT 'Значение оценка за зачёт без аттестаций (0-неявка 2-не_зачтнено 5-зачтено)' AFTER `att_mark_append_ball`;

ALTER TABLE `att_mark_hist` 
ADD COLUMN `simple_mark_exam` TINYINT(3) UNSIGNED NULL COMMENT 'Значение оценка за экзамен без аттестаций' AFTER `simple_mark_test_simple`;

ALTER TABLE `att_mark_hist` 
ADD COLUMN `simple_mark_test_diff` TINYINT(3) UNSIGNED NULL COMMENT 'Значение оценка за зачёт с оценкой без аттестаций' AFTER `simple_mark_exam`;

ALTER TABLE `att_mark_hist` 
ADD COLUMN `simple_mark_course_work` TINYINT(3) UNSIGNED NULL COMMENT 'Значение оценка за курсовую работу без аттестаций' AFTER `simple_mark_test_diff`;

ALTER TABLE `att_mark_hist` 
ADD COLUMN `simple_mark_course_project` TINYINT(3) UNSIGNED NULL COMMENT 'Значение оценка за курсовой проект без аттестаций' AFTER `simple_mark_course_work`;


ALTER TABLE `curriculum_unit` 
ADD COLUMN `has_simple_mark_test_simple` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Допустимо использовать "Значение оценка за зачёт без аттестаций"' AFTER `mark_type`;

ALTER TABLE `curriculum_unit` 
ADD COLUMN `has_simple_mark_exam`  TINYINT(1) NOT NULL DEFAULT 0  COMMENT 'Допустимо использовать "Значение оценка за экзамен без аттестаций"' AFTER `has_simple_mark_test_simple`;

ALTER TABLE `curriculum_unit` 
ADD COLUMN `has_simple_mark_test_diff` TINYINT(1) NOT NULL DEFAULT 0  COMMENT 'Допустимо использовать "Значение оценка за зачёт с оценкой без аттестаций"' AFTER `has_simple_mark_exam`;

ALTER TABLE `curriculum_unit` 
ADD COLUMN `has_simple_mark_course_work` TINYINT(1) NOT NULL DEFAULT 0  COMMENT 'Допустимо использовать "Значение оценка за курсовую работу без аттестаций"' AFTER `has_simple_mark_test_diff`;

ALTER TABLE `curriculum_unit` 
ADD COLUMN `has_simple_mark_course_project` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Допустимо использовать "Значение оценка за курсовой проект без аттестаций"' AFTER `has_simple_mark_course_work`;


ALTER TABLE `curriculum_unit` 
ADD COLUMN `allow_edit_practice_teacher_simple_mark_test_simple` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать "Значение оценка за зачёт без аттестаций"' AFTER `allow_edit_practice_teacher_att_mark_append_ball`;

ALTER TABLE `curriculum_unit` 
ADD COLUMN `allow_edit_practice_teacher_simple_mark_exam` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать "Значение оценка за экзамен без аттестаций"' AFTER `allow_edit_practice_teacher_simple_mark_test_simple`;

ALTER TABLE `curriculum_unit` 
ADD COLUMN `allow_edit_practice_teacher_simple_mark_test_diff` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать "Значение оценка за зачёт с оценкой без аттестаций"' AFTER `allow_edit_practice_teacher_simple_mark_exam`;

ALTER TABLE `curriculum_unit` 
ADD COLUMN `allow_edit_practice_teacher_simple_mark_course_work` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать "Значение оценка за курсовую работу без аттестаций"' AFTER `allow_edit_practice_teacher_simple_mark_test_diff`;

ALTER TABLE `curriculum_unit` 
ADD COLUMN `allow_edit_practice_teacher_simple_mark_course_project` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать "Значение оценка за курсовой проект без аттестаций"' AFTER `allow_edit_practice_teacher_simple_mark_course_work`;


ALTER TABLE `curriculum_unit` 
CHANGE COLUMN `mark_type` `mark_type` ENUM('test_simple', 'exam', 'test_diff', 'no_mark', 'no_att') CHARACTER SET 'latin1' COLLATE 'latin1_general_ci' NOT NULL COMMENT 'Тип отчётности: зачёт, экзамен, зачёт с оценкой, нет, нет аттестаций' ;



ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `allow_edit_practice_teacher_simple_mark_test_simple` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать "Значение оценка за зачёт без аттестаций"' AFTER `allow_edit_practice_teacher_att_mark_append_ball`;

ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `allow_edit_practice_teacher_simple_mark_exam` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать "Значение оценка за экзамен без аттестаций"' AFTER `allow_edit_practice_teacher_simple_mark_test_simple`;

ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `allow_edit_practice_teacher_simple_mark_test_diff` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать "Значение оценка за зачёт с оценкой без аттестаций"' AFTER `allow_edit_practice_teacher_simple_mark_exam`;

ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `allow_edit_practice_teacher_simple_mark_course_work` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать "Значение оценка за курсовую работу без аттестаций"' AFTER `allow_edit_practice_teacher_simple_mark_test_diff`;

ALTER TABLE `curriculum_unit_status_hist` 
ADD COLUMN `allow_edit_practice_teacher_simple_mark_course_project` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Разрешать преподавателю практики редактировать "Значение оценка за курсовой проект без аттестаций"' AFTER `allow_edit_practice_teacher_simple_mark_course_work`;



ALTER TABLE `specialty` 
ADD COLUMN `education_form` ENUM('full-time', 'part-time', 'correspondence') CHARACTER SET 'latin1' COLLATE 'latin1_general_ci' NOT NULL DEFAULT 'full-time' COMMENT 'Форма обучения: очная, очно-заочная, заочная' AFTER `education_level`;


INSERT INTO `specialty` (`specialty_code`, `specialty_name`, `specialization`, `education_level`, `education_form`, `education_standart`, `department_id`, `education_level_order`, `specialty_active`) VALUES ('09.04.02', 'Информационные системы и технологии', 'Цифровые технологии в жизненном цикле изделий (з/о)', 'master', 'correspondence', 'fgos3++', 1600, 2, 1);

commit;



ALTER TABLE `student_from_infosys` 
ADD COLUMN `education_form` ENUM('full-time', 'part-time', 'correspondence') CHARACTER SET 'latin1' COLLATE 'latin1_general_ci' NOT NULL DEFAULT 'full-time' AFTER `specialization`;



CREATE OR REPLACE VIEW `student_vw` AS
    SELECT  
        `s`.`student_id` AS `student_id`,
        `p`.`surname` AS `student_surname`,
        `p`.`firstname` AS `student_firstname`,
        IFNULL(`p`.`middlename`, '') AS `student_middlename`,
        (IFNULL(`sg`.`stud_group_semester`,
                `s`.`student_semestr`) - 1) DIV 2 + 1 AS `course`,
        IFNULL(`sg`.`stud_group_num`, 0) AS `stud_group_num`,
        `sp`.`specialty_code` AS `specialty_code`,
        `sp`.`specialty_name` AS `specialty_name`,
        `sp`.`specialization` AS `specialization`,
        `sp`.`education_form` AS `education_form`,
        `sp`.`education_level` AS `education_level`,
        `sp`.`education_standart` AS `education_standart`,
        `s`.`student_ext_id` AS `student_ext_id`,
        `p`.`gender` AS `gender`,
        `p`.`birthday` AS `birthday`
    FROM
        (((`student` `s`
        JOIN `person` `p` ON (`s`.`person_id` = `p`.`person_id`))
        LEFT JOIN `stud_group` `sg` ON (`s`.`stud_group_id` = `sg`.`stud_group_id`))
        LEFT JOIN `specialty` `sp` ON (`sg`.`specialty_id` = `sp`.`specialty_id`))
    WHERE
        `s`.`student_status` = 'study';
