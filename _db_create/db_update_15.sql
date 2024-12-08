ALTER TABLE `student` DROP COLUMN `stud_group_leader`;
ALTER TABLE `att_mark` 
DROP FOREIGN KEY `fk_att_mark_student_id`;
ALTER TABLE `att_mark` 
ADD CONSTRAINT `fk_att_mark_student_id`
  FOREIGN KEY (`student_id`)
  REFERENCES `student` (`student_id`)
  ON UPDATE CASCADE;
