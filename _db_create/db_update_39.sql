ALTER TABLE `curriculum_unit` 
ADD COLUMN `department_id` INT UNSIGNED NULL COMMENT 'Ссылка на ответственную кафедру' AFTER `stud_group_id`;

set sql_safe_updates=0;
update curriculum_unit cu set cu.department_id = (select t.department_id from teacher t where t.teacher_id = cu.teacher_id);
update curriculum_unit set department_id=1605 where curriculum_unit_id in (1867, 1868);
commit;
ALTER TABLE `curriculum_unit` 
CHANGE COLUMN `department_id` `department_id` INT UNSIGNED NOT NULL COMMENT 'Ссылка на ответственную кафедру' ;

CREATE TABLE `teacher_department_part_time_job` (
  `teacher_id` INT UNSIGNED NOT NULL,
  `department_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`teacher_id`, `department_id`),
  CONSTRAINT `teacher_department_fk_teacher`
    FOREIGN KEY (`teacher_id`)
    REFERENCES `teacher` (`teacher_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `teacher_department_fk_department`
    FOREIGN KEY (`department_id`)
    REFERENCES `department` (`department_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
COMMENT = 'Кафедры на которых преподаватель работает по совместительству';

INSERT INTO `teacher_department_part_time_job` (`teacher_id`, `department_id`) VALUES (205, 1605);
commit;


