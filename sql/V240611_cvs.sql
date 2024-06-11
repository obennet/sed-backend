# DSM
CREATE TABLE IF NOT EXISTS `seddb`.`cvs_dsm_files`
(
    `vcs` INT UNSIGNED NOT NULL,
    `file` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`vcs`),
    FOREIGN KEY (`vcs`)
        REFERENCES `seddb`.`cvs_vcss`(`id`)
        ON DELETE CASCADE,
    FOREIGN KEY(`file`)
      REFERENCES `seddb`.`files`(`id`)
      ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS `seddb`.`cvs_formulas_external_factors`
(
    `vcs_row`         INT UNSIGNED NOT NULL,
    `design_group`    INT UNSIGNED NOT NULL,
    `external_factor` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`vcs_row`, `design_group`, `external_factor`),
    FOREIGN KEY (`vcs_row`)
        REFERENCES `seddb`.`cvs_design_mi_formulas` (`vcs_row`)
        ON DELETE CASCADE,
    FOREIGN KEY (`design_group`)
        REFERENCES `seddb`.`cvs_design_mi_formulas` (`design_group`)
        ON DELETE CASCADE,
    FOREIGN KEY (`external_factor`)
        REFERENCES `seddb`.`cvs_market_inputs` (`id`)
        ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS `seddb`.`cvs_formulas_value_drivers`
(
    `vcs_row`      INT UNSIGNED NOT NULL,
    `design_group` INT UNSIGNED NOT NULL,
    `value_driver` INT UNSIGNED NOT NULL,
    `project`      INT UNSIGNED NOT NULL,
    PRIMARY KEY (`vcs_row`, `design_group`, `value_driver`),
    FOREIGN KEY (`vcs_row`)
        REFERENCES `seddb`.`cvs_design_mi_formulas` (`vcs_row`)
        ON DELETE CASCADE,
    FOREIGN KEY (`design_group`)
        REFERENCES `seddb`.`cvs_design_mi_formulas` (`design_group`)
        ON DELETE CASCADE,
    FOREIGN KEY (`value_driver`)
        REFERENCES `seddb`.`cvs_value_drivers` (`id`)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `seddb`.`cvs_simulation_files`
(
    `project_id` INT UNSIGNED NOT NULL,
    `file` INT UNSIGNED NOT NULL,
    `insert_timestamp` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `vs_x_ds` TEXT NOT NULL,
    PRIMARY KEY (`file`),
    FOREIGN KEY (`project_id`)
        REFERENCES `seddb`.`cvs_projects`(`id`)
        ON DELETE CASCADE,
    FOREIGN KEY(`file`)
      REFERENCES `seddb`.`files`(`id`)
      ON DELETE CASCADE
);