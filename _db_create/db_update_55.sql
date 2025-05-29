ALTER TABLE `student` 
ADD COLUMN `financing` ENUM('budget', 'contract') NOT NULL DEFAULT 'budget' COMMENT 'Источник финансирования' AFTER `student_status`;

ALTER TABLE `student_from_infosys` 
ADD COLUMN `financing` ENUM('budget', 'contract') NOT NULL DEFAULT 'budget' COMMENT 'Источник финансирования';

ALTER TABLE `person` DROP COLUMN `allow_jwt_auth`;
ALTER TABLE `person_hist` DROP COLUMN `allow_jwt_auth`;

CREATE OR REPLACE
VIEW `student_vw` AS
    SELECT 
        `s`.`student_id` AS `student_id`,
        `p`.`surname` AS `student_surname`,
        `p`.`firstname` AS `student_firstname`,
        IFNULL(`p`.`middlename`, '') AS `student_middlename`,
        (`s`.`student_semestr` - 1) DIV 2 + 1 AS `course`,
        IFNULL(`sg`.`stud_group_num`, 0) AS `stud_group_num`,
        `sp`.`specialty_code` AS `specialty_code`,
        `sp`.`specialty_name` AS `specialty_name`,
        `sp`.`specialization` AS `specialization`,
        `sp`.`education_form` AS `education_form`,
        `sp`.`education_level` AS `education_level`,
        `sp`.`education_standart` AS `education_standart`,
        `s`.`student_ext_id` AS `student_ext_id`,
        `p`.`gender` AS `gender`,
        `p`.`birthday` AS `birthday`,
        `s`.`financing` AS `financing`
    FROM
        (((`student` `s`
        JOIN `person` `p` ON (`s`.`person_id` = `p`.`person_id`))
        JOIN `specialty` `sp` ON (`s`.`specialty_id` = `sp`.`specialty_id`))
        LEFT JOIN `stud_group` `sg` ON (`s`.`stud_group_id` = `sg`.`stud_group_id`))
    WHERE
        `s`.`student_status` = 'study';
