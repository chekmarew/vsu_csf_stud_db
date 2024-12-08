CREATE TABLE `exam` (
  `exam_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `curriculum_unit_id` INT UNSIGNED NOT NULL,
  `stud_group_subnums` TINYINT UNSIGNED NOT NULL DEFAULT 0,
  `exam_stime` DATETIME NOT NULL,
  `exam_etime` DATETIME NOT NULL,
  PRIMARY KEY (`exam_id`),
  UNIQUE INDEX `exam_UNIQUE` (`curriculum_unit_id` ASC, `stud_group_subnums` ASC),
  CONSTRAINT `fk_cu_exam`
    FOREIGN KEY (`curriculum_unit_id`)
    REFERENCES `curriculum_unit` (`curriculum_unit_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
COMMENT = 'Расписание экзаменов';


ALTER TABLE `exam` 
ADD COLUMN `teacher_id` INT UNSIGNED NOT NULL AFTER `exam_etime`,
ADD INDEX `fk_teacher_exam_idx` (`teacher_id` ASC) VISIBLE;

ALTER TABLE `exam` 
ADD CONSTRAINT `fk_teacher_exam`
  FOREIGN KEY (`teacher_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;

CREATE TABLE `classroom` (
  `classroom` VARCHAR(6) CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_general_ci' NOT NULL,
  PRIMARY KEY (`classroom`))
COMMENT = 'Аудитория';

INSERT INTO `classroom` (`classroom`) VALUES ('292');
INSERT INTO `classroom` (`classroom`) VALUES ('305П');
INSERT INTO `classroom` (`classroom`) VALUES ('307П');
INSERT INTO `classroom` (`classroom`) VALUES ('380');
INSERT INTO `classroom` (`classroom`) VALUES ('477');
INSERT INTO `classroom` (`classroom`) VALUES ('479');
INSERT INTO `classroom` (`classroom`) VALUES ('505П');
INSERT INTO `classroom` (`classroom`) VALUES ('290');
INSERT INTO `classroom` (`classroom`) VALUES ('291');
INSERT INTO `classroom` (`classroom`) VALUES ('293');
INSERT INTO `classroom` (`classroom`) VALUES ('295');
INSERT INTO `classroom` (`classroom`) VALUES ('297');
INSERT INTO `classroom` (`classroom`) VALUES ('301П');
INSERT INTO `classroom` (`classroom`) VALUES ('303П');
INSERT INTO `classroom` (`classroom`) VALUES ('314П');
INSERT INTO `classroom` (`classroom`) VALUES ('316П');
INSERT INTO `classroom` (`classroom`) VALUES ('381');
INSERT INTO `classroom` (`classroom`) VALUES ('382');
INSERT INTO `classroom` (`classroom`) VALUES ('383');
INSERT INTO `classroom` (`classroom`) VALUES ('384');
INSERT INTO `classroom` (`classroom`) VALUES ('385');
INSERT INTO `classroom` (`classroom`) VALUES ('387');
INSERT INTO `classroom` (`classroom`) VALUES ('190А');
INSERT INTO `classroom` (`classroom`) VALUES ('308П');
INSERT INTO `classroom` (`classroom`) VALUES ('309П');
commit;

ALTER TABLE `classroom` 
COLLATE = utf8mb4_general_ci ;


ALTER TABLE `exam` 
ADD COLUMN `classroom` VARCHAR(6) CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_general_ci' NULL AFTER `teacher_id`,
ADD COLUMN `exam_comment` VARCHAR(4000) NULL COMMENT 'Комментарий к экзамену' AFTER `classroom`;


ALTER TABLE `exam` 
ADD INDEX `fk_classroom_exam_idx` (`classroom` ASC) VISIBLE;

ALTER TABLE `exam` 
ADD CONSTRAINT `fk_classroom_exam`
  FOREIGN KEY (`classroom`)
  REFERENCES `classroom` (`classroom`)
  ON DELETE SET NULL
  ON UPDATE CASCADE;
  
 ALTER TABLE exam add CONSTRAINT exam_time_chk CHECK (TIME_TO_SEC(TIMEDIFF(exam_etime, exam_stime)) between 3600 and 28800);


