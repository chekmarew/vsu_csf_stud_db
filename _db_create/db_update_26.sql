set sql_safe_updates=0;

update stud_group set stud_group_num=stud_group_num*10+stud_group_subnum where stud_group_subnum>0;
commit;

ALTER TABLE `stud_group` 
DROP COLUMN `stud_group_subnum`,
DROP INDEX `UNIQUE` ,
ADD UNIQUE INDEX `UNIQUE` (`stud_group_year` ASC, `stud_group_semester` ASC, `stud_group_num` ASC) VISIBLE;



CREATE TABLE `curriculum_unit_practice_teacher` (
  `curriculum_unit_id` INT UNSIGNED NOT NULL,
  `teacher_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`curriculum_unit_id`, `teacher_id`),

  CONSTRAINT `curriculum_unit_practice_teacher_fk1`
    FOREIGN KEY (`curriculum_unit_id`)
    REFERENCES `curriculum_unit` (`curriculum_unit_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `curriculum_unit_practice_teacher_fk2`
    FOREIGN KEY (`teacher_id`)
    REFERENCES `teacher` (`teacher_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
COMMENT = 'Преподаватель практики для единицы учебного плана';



CREATE TABLE `curriculum_unit_practice_teacher_hist` (
  `curriculum_unit_id` INT UNSIGNED NOT NULL,
  `stime` DATETIME NOT NULL,
  `teacher_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`curriculum_unit_id`, `stime`, `teacher_id`),


  CONSTRAINT `curriculum_unit_practice_teacher_hist_fk1`
    FOREIGN KEY (`teacher_id`)
    REFERENCES `teacher` (`teacher_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
COMMENT = 'Преподаватель практики для единицы учебного плана (история)';

ALTER TABLE `curriculum_unit_practice_teacher_hist` 
ADD CONSTRAINT `curriculum_unit_practice_teacher_hist_fk2`
  FOREIGN KEY (`curriculum_unit_id` , `stime`)
  REFERENCES `curriculum_unit_status_hist` (`curriculum_unit_id` , `stime`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;



insert into curriculum_unit_practice_teacher 
select curriculum_unit_id, practice_teacher_id as teacher_id from curriculum_unit where practice_teacher_id is not null;

insert into curriculum_unit_practice_teacher_hist
select curriculum_unit_id, stime, practice_teacher_id as teacher_id from curriculum_unit_status_hist where practice_teacher_id is not null;

commit;


ALTER TABLE `curriculum_unit` 
DROP FOREIGN KEY `fk_curriculum_unit_practice_teacher`;
ALTER TABLE `curriculum_unit` 
DROP COLUMN `practice_teacher_id`,
DROP INDEX `fk_curriculum_unit_practice_teacher_idx` ;
;

ALTER TABLE `curriculum_unit_status_hist` 
DROP FOREIGN KEY `fk_curriculum_unit_status_hist_practice_teacher`;
ALTER TABLE `curriculum_unit_status_hist` 
DROP COLUMN `practice_teacher_id`,
DROP INDEX `fk_curriculum_unit_status_hist_practice_teacher_idx` ;
;

ALTER TABLE `teacher` 
ADD CONSTRAINT `fk_teacher_department`
  FOREIGN KEY (`department_id`)
  REFERENCES `department` (`department_id`)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION;