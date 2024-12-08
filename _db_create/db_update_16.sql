ALTER TABLE `stud_group` 
ADD COLUMN `curator_id` INT(11) UNSIGNED NULL COMMENT 'Куратор группы',
ADD COLUMN `group_leader_id` BIGINT UNSIGNED NULL COMMENT 'Староста группы',
ADD COLUMN `group_leader2_id` BIGINT UNSIGNED NULL COMMENT 'Староста группы 2';

ALTER TABLE `stud_group`
ADD INDEX `fk_curator_id_idx` (`curator_id`),
ADD INDEX `fk_group_leader_idx` (`group_leader_id`),
ADD INDEX `fk_group_leader2_idx` (`group_leader2_id`);

ALTER TABLE `stud_group` 
ADD CONSTRAINT `fk_curator_id`
  FOREIGN KEY (`curator_id`)
  REFERENCES `teacher` (`teacher_id`)
  ON DELETE SET NULL
  ON UPDATE CASCADE,
ADD CONSTRAINT `fk_group_leader`
  FOREIGN KEY (`group_leader_id`)
  REFERENCES `student` (`student_id`)
  ON DELETE SET NULL
  ON UPDATE CASCADE,
ADD CONSTRAINT `fk_group_leader2`
  FOREIGN KEY (`group_leader2_id`)
  REFERENCES `student` (`student_id`)
  ON DELETE SET NULL
  ON UPDATE CASCADE;