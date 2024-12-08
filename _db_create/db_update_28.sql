CREATE TABLE `person` (
  `person_id` INT(11) unsigned NOT NULL COMMENT 'ID человека',
  `surname` varchar(45) NOT NULL COMMENT 'Фамилия',
  `firstname` varchar(45) NOT NULL COMMENT 'Имя',
  `middlename` varchar(45) DEFAULT NULL COMMENT 'Отчество',
  `login` varchar(45) DEFAULT NULL COMMENT 'Учётное имя',
  `card_number` bigint(20) unsigned DEFAULT NULL COMMENT 'Номер карты (пропуск)',
  `email` varchar(45) DEFAULT NULL COMMENT 'E-mail',
  `phone` bigint(20) unsigned DEFAULT NULL COMMENT 'Сотовый телефон',
  `contacts` varchar(4000) DEFAULT NULL COMMENT 'Доп. контактные данные',
  PRIMARY KEY (`person_id`),
  UNIQUE KEY `login_UNIQUE` (`login`),
  UNIQUE KEY `card_number_UNIQUE` (`card_number`),
  UNIQUE KEY `email_UNIQUE` (`email`),
  UNIQUE KEY `phone_UNIQUE` (`phone`)
) ENGINE=InnoDB;


insert into person
	select teacher_id, teacher_surname, teacher_firstname, teacher_middlename, teacher_login, null, teacher_email, teacher_phone, teacher_contacts from teacher;
commit;

ALTER TABLE `teacher` 
ADD COLUMN `person_id` INT(11) UNSIGNED NULL COMMENT 'Ссылка на person_id' AFTER `teacher_id`,
ADD INDEX `fk_teacher_person_idx` (`person_id` ASC) VISIBLE;

ALTER TABLE `teacher` 
ADD CONSTRAINT `fk_teacher_person`
  FOREIGN KEY (`person_id`)
  REFERENCES `person` (`person_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;
  
 insert into person
	select 12, admin_user_surname, admin_user_firstname, admin_user_middlename, admin_user_login, null, admin_user_email, admin_user_phone, admin_user_contacts from admin_user where admin_user_id=5;
	
set sql_safe_updates=0;
update teacher set person_id=teacher_id;
commit;


ALTER TABLE `teacher` 
CHANGE COLUMN `person_id` `person_id` INT(11) UNSIGNED NOT NULL COMMENT 'Ссылка на person_id' ;

ALTER TABLE `admin_user` 
ADD COLUMN `person_id` INT(11) UNSIGNED NULL COMMENT 'Ссылка на person_id' AFTER `admin_user_id`;

UPDATE `admin_user` SET `person_id` = '12' WHERE (`admin_user_id` = '5');
UPDATE `admin_user` SET `person_id` = '17' WHERE (`admin_user_id` = '3');
UPDATE `admin_user` SET `person_id` = '18' WHERE (`admin_user_id` = '6');
commit;

ALTER TABLE `admin_user` 
CHANGE COLUMN `person_id` `person_id` INT(11) UNSIGNED NOT NULL COMMENT 'Ссылка на person_id',
ADD INDEX `fk_admin_user_person_idx` (`person_id` ASC) VISIBLE;

ALTER TABLE `admin_user` 
ADD CONSTRAINT `fk_admin_user_person`
  FOREIGN KEY (`person_id`)
  REFERENCES `person` (`person_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;



ALTER TABLE `admin_user` 
DROP INDEX `admin_user_phone_UNIQUE` ,
DROP INDEX `admin_user_email_UNIQUE` ,
DROP INDEX `admin_user_login_UNIQUE`,
DROP COLUMN `admin_user_contacts`,
DROP COLUMN `admin_user_phone`,
DROP COLUMN `admin_user_email`,
DROP COLUMN `admin_user_login`,
DROP COLUMN `admin_user_middlename`,
DROP COLUMN `admin_user_firstname`,
DROP COLUMN `admin_user_surname` ;



ALTER TABLE `teacher` 
DROP INDEX `teacher_phone_UNIQUE` ,
DROP INDEX `teacher_email_UNIQUE` ,
DROP INDEX `teacher_login_UNIQUE` ,
DROP COLUMN `teacher_contacts`,
DROP COLUMN `teacher_phone`,
DROP COLUMN `teacher_email`,
DROP COLUMN `teacher_login`,
DROP COLUMN `teacher_middlename`,
DROP COLUMN `teacher_firstname`,
DROP COLUMN `teacher_surname` ;

SET FOREIGN_KEY_CHECKS = 0;
ALTER TABLE `person` 
CHANGE COLUMN `person_id` `person_id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID человека' ;
SET FOREIGN_KEY_CHECKS = 1;


ALTER TABLE student CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE person CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

update person p set p.login=(select s.student_login from student s where p.`surname` = s.`student_surname` and p.`firstname`=s.`student_firstname` and p.`middlename`=s.`student_middlename`) 
where exists (select * from student s2 where p.`surname` = s2.`student_surname` and p.`firstname`=s2.`student_firstname` and p.`middlename`=s2.`student_middlename`) and p.login is null;
commit;


ALTER TABLE `student` 
ADD COLUMN `person_id` INT(11) UNSIGNED NULL COMMENT 'Ссылка на person_id' AFTER `student_id`;


update student s set s.person_id=(select p.person_id from person p where p.`surname` = s.`student_surname` and p.`firstname`=s.`student_firstname` and p.`middlename`=s.`student_middlename`) 
where exists (select * from person p2 where p2.`surname` = s.`student_surname` and p2.`firstname`=s.`student_firstname` and p2.`middlename`=s.`student_middlename`);


insert into person
	select null, student_surname, student_firstname, student_middlename, student_login, card_number, student_email, student_phone, student_contacts  from student where person_id is null;
	
update student s set s.person_id=(select p.person_id from person p where p.`surname` = s.`student_surname` and p.`firstname`=s.`student_firstname` and ifnull(p.`middlename`,'')=ifnull(s.`student_middlename`,''))
where exists (select * from person p2 where p2.`surname` = s.`student_surname` and p2.`firstname`=s.`student_firstname` and ifnull(p2.`middlename`,'')=ifnull(s.`student_middlename`,''));

commit;

ALTER TABLE `student` 
CHANGE COLUMN `person_id` `person_id` INT(11) UNSIGNED NOT NULL COMMENT 'Ссылка на person_id' ;


ALTER TABLE `student` 
ADD INDEX `fk_student_person_idx` (`person_id` ASC) VISIBLE;

ALTER TABLE `student` 
ADD CONSTRAINT `fk_student_person`
  FOREIGN KEY (`person_id`)
  REFERENCES `person` (`person_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;
  
  
 
ALTER TABLE `student`
DROP INDEX `student_phone_UNIQUE` ,
DROP INDEX `student_email_UNIQUE` ,
DROP INDEX `card_number_UNIQUE` ,
DROP INDEX `student_login_UNIQUE` ,
DROP COLUMN `student_contacts`,
DROP COLUMN `student_phone`,
DROP COLUMN `student_email`,
DROP COLUMN `card_number`,
DROP COLUMN `student_login`,
DROP COLUMN `student_middlename`,
DROP COLUMN `student_firstname`,
DROP COLUMN `student_surname`;


ALTER TABLE `att_mark_hist` ADD COLUMN `changed_person_id` INT(11) UNSIGNED NULL AFTER `etime`;

set sql_safe_updates=0;
update att_mark_hist h set h.changed_person_id = (select u.person_id from admin_user u where u.admin_user_id =h.admin_user_id) where h.admin_user_id is not null;
update att_mark_hist h set h.changed_person_id = (select u.person_id from teacher u where u.teacher_id = h.teacher_id) where h.teacher_id is not null;
commit;



ALTER TABLE `att_mark_hist` 
DROP FOREIGN KEY `fk_att_mark_hist_teacher_id`,
DROP FOREIGN KEY `fk_att_mark_hist_admin_user_id`;
ALTER TABLE `att_mark_hist` 
DROP INDEX `fk_att_mark_hist_teacher_id_idx` ,
DROP INDEX `fk_att_mark_hist_admin_user_id_idx` ,
DROP COLUMN `teacher_id`,
DROP COLUMN `admin_user_id` ;

ALTER TABLE `att_mark_hist` CHANGE COLUMN `changed_person_id` `changed_person_id` INT(11) UNSIGNED NOT NULL COMMENT 'Ссылка на person_id' ;

ALTER TABLE `att_mark_hist` 
ADD INDEX `fk_att_mark_hist_person_idx` (`changed_person_id` ASC) VISIBLE;

ALTER TABLE `att_mark_hist` 
ADD CONSTRAINT `fk_att_mark_hist_person`
  FOREIGN KEY (`changed_person_id`)
  REFERENCES `person` (`person_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;




ALTER TABLE `curriculum_unit_status_hist` ADD COLUMN `changed_person_id` INT(11) UNSIGNED NULL AFTER `etime`;

set sql_safe_updates=0;
update curriculum_unit_status_hist h set h.changed_person_id = (select u.person_id from admin_user u where u.admin_user_id =h.admin_user_id) where h.admin_user_id is not null;
update curriculum_unit_status_hist h set h.changed_person_id = (select u.person_id from teacher u where u.teacher_id = h.teacher_id) where h.teacher_id is not null;
commit;



ALTER TABLE `fkn_att_test`.`curriculum_unit_status_hist` 
DROP FOREIGN KEY `fk_curriculum_unit_status_teacher_id`,
DROP FOREIGN KEY `fk_curriculum_unit_status_hist_admin_user_id`;
ALTER TABLE `fkn_att_test`.`curriculum_unit_status_hist` 
DROP INDEX `fk_curriculum_unit_status_teacher_id_idx` ,
DROP INDEX `fk_curriculum_unit_status_hist_admin_user_id_idx` ,
DROP COLUMN `teacher_id`,
DROP COLUMN `admin_user_id`;


ALTER TABLE `curriculum_unit_status_hist` CHANGE COLUMN `changed_person_id` `changed_person_id` INT(11) UNSIGNED NOT NULL COMMENT 'Ссылка на person_id' ;

ALTER TABLE `curriculum_unit_status_hist` 
ADD INDEX `fk_curriculum_unit_status_hist_person_idx` (`changed_person_id` ASC) VISIBLE;

ALTER TABLE `curriculum_unit_status_hist` 
ADD CONSTRAINT `fk_curriculum_unit_status_hist_person`
  FOREIGN KEY (`changed_person_id`)
  REFERENCES `person` (`person_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;



CREATE 
 OR REPLACE VIEW `student_vw` AS
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
        `sp`.`education_level` AS `education_level`,
        `sp`.`education_standart` AS `education_standart`
    FROM
        (((`student` `s` join `person` p on `s`.`person_id`=`p`.`person_id` )
        LEFT JOIN `stud_group` `sg` ON (`s`.`stud_group_id` = `sg`.`stud_group_id`))
        LEFT JOIN `specialty` `sp` ON (`sg`.`specialty_id` = `sp`.`specialty_id`))
        
    WHERE
        `s`.`student_status` = 'study';
		
		
create table person_hist
select
	person_id, 
	now() stime, 
	cast(null as datetime) etime,
    cast(17 as UNSIGNED INTEGER) changed_person_id,
    surname, firstname, middlename, login, card_number, email, phone, contacts    

from person;

ALTER TABLE `person_hist` ADD PRIMARY KEY (`person_id`, `stime`);


ALTER TABLE `person_hist` 
CHANGE COLUMN `changed_person_id` `changed_person_id` INT(11) UNSIGNED NULL COMMENT 'Ссылка на person_id, человека изменившего запись' ;

ALTER TABLE `person_hist` 
ADD INDEX `fk_changed_person_idx` (`changed_person_id` ASC) VISIBLE;

ALTER TABLE `person_hist` 
ADD CONSTRAINT `fk_person_hist_changed_person`
  FOREIGN KEY (`changed_person_id`)
  REFERENCES `person` (`person_id`)
  ON DELETE SET NULL
  ON UPDATE CASCADE;
  
ALTER TABLE `person_hist` 
ADD CONSTRAINT `fk_person_hist_person`
  FOREIGN KEY (`person_id`)
  REFERENCES `person` (`person_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;
  
  
ALTER TABLE `teacher` 
ADD UNIQUE INDEX `person_id_UNIQUE` (`person_id` ASC) VISIBLE;

ALTER TABLE `admin_user` 
ADD UNIQUE INDEX `person_id_UNIQUE` (`person_id` ASC) VISIBLE;
