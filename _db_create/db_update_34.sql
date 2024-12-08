ALTER TABLE `student` 
ADD COLUMN `student_ext_id` BIGINT UNSIGNED NULL COMMENT 'Код учебной деятельности INFOSYS' AFTER `person_id`,
ADD UNIQUE INDEX `student_ext_id_UNIQUE` (`student_ext_id` ASC) VISIBLE;


truncate table student_from_infosys;

ALTER TABLE `student_from_infosys` 
ADD COLUMN `student_ext_id` BIGINT NOT NULL AFTER `education_standart`,
ADD COLUMN `gender` ENUM('M', 'W') NOT NULL AFTER `student_ext_id`,
ADD COLUMN `birthday` DATE NOT NULL AFTER `gender`,
CHANGE COLUMN `education_level` `education_level` ENUM('bachelor', 'specialist', 'master') NOT NULL DEFAULT 'bachelor' COMMENT 'Уровень образования (бакалавр или специалист)';


ALTER TABLE `specialty` 
CHANGE COLUMN `education_level` `education_level` ENUM('bachelor', 'specialist', 'master') NOT NULL DEFAULT 'bachelor' COMMENT 'Уровень образования (бакалавр или специалист)' ;

CREATE 
     OR REPLACE VIEW `student_vw` AS
        SELECT 
        `s`.`student_id` AS `student_id`,
        `p`.`surname` AS `student_surname`,
        `p`.`firstname` AS `student_firstname`,
        IFNULL(`p`.`middlename`, '') AS `student_middlename`,
        (((IFNULL(`sg`.`stud_group_semester`,
                `s`.`student_semestr`) - 1) DIV 2) + 1) AS `course`,
        IFNULL(`sg`.`stud_group_num`, 0) AS `stud_group_num`,
        `sp`.`specialty_code` AS `specialty_code`,
        `sp`.`specialty_name` AS `specialty_name`,
        `sp`.`specialization` AS `specialization`,
        `sp`.`education_level` AS `education_level`,
        `sp`.`education_standart` AS `education_standart`,
        `s`.`student_ext_id` AS `student_ext_id`,
        `p`.`gender` AS `gender`,
        `p`.`birthday` AS `birthday`
        FROM
        (((`student` `s`
        JOIN `person` `p` ON ((`s`.`person_id` = `p`.`person_id`)))
        LEFT JOIN `stud_group` `sg` ON ((`s`.`stud_group_id` = `sg`.`stud_group_id`)))
        LEFT JOIN `specialty` `sp` ON ((`sg`.`specialty_id` = `sp`.`specialty_id`)))
    WHERE
        (`s`.`student_status` = 'study');



