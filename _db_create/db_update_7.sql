ALTER TABLE `att_mark_hist` 
DROP FOREIGN KEY `fk_att_mark_hist_att_mark_id`;
ALTER TABLE `att_mark_hist` 
CHANGE COLUMN `att_mark_id` `att_mark_id` BIGINT UNSIGNED NOT NULL COMMENT 'Ссылка на att_mark(att_mark_id)' ;
ALTER TABLE `att_mark` 
CHANGE COLUMN `att_mark_id` `att_mark_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID' ;


ALTER TABLE `att_mark_hist` 
ADD CONSTRAINT `fk_att_mark_hist_att_mark_id`
  FOREIGN KEY (`att_mark_id`)
  REFERENCES `att_mark` (`att_mark_id`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;
  
