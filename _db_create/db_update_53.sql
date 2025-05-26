ALTER TABLE `att_mark`
ADD COLUMN `att_mark_manual_add`  TINYINT(1) NOT NULL DEFAULT 0;

ALTER TABLE `att_mark`
ADD COLUMN `att_mark_group_subnum` TINYINT(3) UNSIGNED NULL;