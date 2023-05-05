CREATE TABLE `seddb`.`sso_tokens` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `expiration` DATETIME(3) NOT NULL DEFAULT (CURRENT_TIMESTAMP(3) + INTERVAL 30 SECOND),
  `ip` VARCHAR(45) NOT NULL,
  `user_id` INT UNSIGNED NOT NULL,
  `nonce` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`));

CREATE EVENT AutoDeleteOldSSOTokens
ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 10 MINUTE
ON COMPLETION PRESERVE
DO
DELETE FROM `seddb`.`sso_tokens` WHERE expiration < NOW();