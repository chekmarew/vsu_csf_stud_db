CREATE TABLE `subject` (
  `subject_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'ID предмета',
  `subject_name` varchar(64) NOT NULL COMMENT 'Наименование предмета',
  PRIMARY KEY (`subject_id`),
  UNIQUE KEY `subject_name_UNIQUE` (`subject_name`)
) COMMENT='Предмет';

CREATE TABLE `teacher` (
  `teacher_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'ID преподавателя',
  `teacher_surname` varchar(45) NOT NULL COMMENT 'Фамилия преподавателя',
  `teacher_firstname` varchar(45) NOT NULL COMMENT 'Имя преподавателя',
  `teacher_middlename` varchar(45) DEFAULT NULL COMMENT 'Отчество преподавателя',
  `teacher_rank` varchar(45) NOT NULL COMMENT 'Должность преподавателя(ассистент, ст. преподаватель, доцент, профессор)',
  PRIMARY KEY (`teacher_id`)
) COMMENT='Преподаватель';

CREATE TABLE `stud_group` (
  `stud_group_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'первичный ключ',
  `stud_group_year` year(4) NOT NULL COMMENT 'Учебный год',
  `stud_group_semester` tinyint(3) unsigned NOT NULL COMMENT 'Семестр (отсчёт с 1 курса)',
  `stud_group_num` tinyint(3) unsigned NOT NULL COMMENT 'Номер группы',
  `stud_group_subnum` tinyint(3) unsigned DEFAULT NULL COMMENT 'Номер подгруппы',
  PRIMARY KEY (`stud_group_id`)  
) COMMENT='Студенческая группа на определ. учебный год и семестр';



CREATE TABLE `curriculum_unit` (
  `curriculum_unit_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'ID единицы учебного плана',
  `subject_id` int(11) unsigned NOT NULL COMMENT 'ID предмета из таблицы subject',
  `stud_group_id` int(11) unsigned NOT NULL COMMENT 'ID студенчкской группы в опред. учебн. году и семестре из таблицы  stud_group',
  `teacher_id` int(11) unsigned NOT NULL COMMENT 'ID преподавателя  из таблицы teacher',
  `mark_type` tinyint(3) unsigned NOT NULL COMMENT 'Тип отчётности 1 - зачёт; 2-экзамен; 3-зачёт с оценкой',
  PRIMARY KEY (`curriculum_unit_id`),
  UNIQUE KEY `UNIQUE` (`subject_id`,`stud_group_id`),
  KEY `subject_id` (`subject_id`),
  KEY `stud_group_id` (`stud_group_id`),
  KEY `teacher_id` (`teacher_id`),
  CONSTRAINT `fk_curriculum_unit_stud_group` FOREIGN KEY (`stud_group_id`) REFERENCES `stud_group` (`stud_group_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_curriculum_unit_subject` FOREIGN KEY (`subject_id`) REFERENCES `subject` (`subject_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_curriculum_unit_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teacher` (`teacher_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) COMMENT='Единица учебного плана';



CREATE TABLE `student` (
  `student_id` bigint(20) unsigned NOT NULL COMMENT 'Номер студенческого билета',
  `student_surname` varchar(45) NOT NULL COMMENT 'Фамилия студента',
  `student_firstname` varchar(45) NOT NULL COMMENT 'Имя студента',
  `student_middlename` varchar(45) DEFAULT NULL COMMENT 'Отчество студента',
  `stud_group_id` int(11) unsigned DEFAULT NULL COMMENT 'ID студенческой группы из таблицы stud_group если NULL, то студент выпускник или отчислен',
  PRIMARY KEY (`student_id`),
  KEY `stud_group_id` (`stud_group_id`),
  CONSTRAINT `fk_student_stud_group` FOREIGN KEY (`stud_group_id`) REFERENCES `stud_group` (`stud_group_id`) ON DELETE SET NULL ON UPDATE SET NULL
);




CREATE TABLE `att_mark` (
  `att_mark_id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `curriculum_unit_id` int(11) unsigned NOT NULL COMMENT 'ID единицы учебного плана из таблицы curriculum_unit',
  `student_id` bigint(20) unsigned NOT NULL COMMENT 'Номер студенческого билета',
  `att_mark_1` tinyint(3) unsigned DEFAULT NULL COMMENT 'Оценка за 1ю аттестацию',
  `att_mark_2` tinyint(3) unsigned DEFAULT NULL COMMENT 'Оценка за 2ю аттестацию',
  `att_mark_3` tinyint(3) unsigned DEFAULT NULL COMMENT 'Оценка за 3ю аттестацию',
  `att_mark_append_ball` tinyint(3) unsigned DEFAULT NULL COMMENT 'Дополнительный балл',
  PRIMARY KEY (`att_mark_id`),
  UNIQUE KEY `UNIQUE` (`curriculum_unit_id`,`student_id`),
  KEY `fk_att_mark_student_id_idx` (`student_id`),
  CONSTRAINT `fk_att_mark_curriculum_unit_id` FOREIGN KEY (`curriculum_unit_id`) REFERENCES `curriculum_unit` (`curriculum_unit_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_att_mark_student_id` FOREIGN KEY (`student_id`) REFERENCES `student` (`student_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) COMMENT='Оценки за аттестации';



-- fix DB
ALTER TABLE `curriculum_unit` 
ADD COLUMN `hours_att_1` TINYINT UNSIGNED NOT NULL COMMENT 'Кол-во часов на 1-ю аттестацю' AFTER `mark_type`,
ADD COLUMN `hours_att_2` TINYINT UNSIGNED NOT NULL COMMENT 'Кол-во часов на 2-ю аттестацю' AFTER `hours_att_1`,
ADD COLUMN `hours_att_3` TINYINT UNSIGNED NOT NULL COMMENT 'Кол-во часов на 3-ю аттестацю' AFTER `hours_att_2`;


ALTER TABLE `att_mark` 
ADD COLUMN `att_mark_exam` TINYINT UNSIGNED NULL COMMENT 'Оценка за экзамен' AFTER `att_mark_3`;



ALTER TABLE `stud_group` 
ADD COLUMN `stud_group_active` TINYINT(1) UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Флаг: Действующая студенческая группа' AFTER `stud_group_subnum`;
ALTER TABLE `stud_group` ADD UNIQUE INDEX `UNIQUE` (`stud_group_year` ASC, `stud_group_semester`, `stud_group_num`, `stud_group_subnum`);

ALTER TABLE `stud_group` 
CHANGE COLUMN `stud_group_subnum` `stud_group_subnum` TINYINT(3) UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Номер подгруппы (если нет подгрупп, то =0)' ;


ALTER TABLE `student` 
ADD COLUMN `student_semestr` TINYINT(3) NULL COMMENT 'Семестр (отсчёт с 1 курса)' AFTER `stud_group_id`;

ALTER TABLE `student` 
ADD COLUMN `student_alumnus_year` YEAR(4) NULL COMMENT 'Год в котором выпустился студент' AFTER `student_semestr`,
ADD COLUMN `student_expelled_year` YEAR(4) NULL COMMENT 'Учебный год, в котором отчислили студента или он ушёл в академ. отпуск. После восстановления поле is null' AFTER `student_alumnus_year`;