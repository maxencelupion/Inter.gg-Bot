DROP DATABASE IF EXISTS `discord_lol`;

CREATE DATABASE IF NOT EXISTS `discord_lol`;

USE `discord_lol`;

DROP TABLE IF EXISTS `guild_init`;

DROP TABLE IF EXISTS `users_lol`;

CREATE TABLE IF NOT EXISTS `guild_init` (
    `server_id` varchar(255) NOT NULL PRIMARY KEY,
    `channel_id` varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS `users_lol` (
    `lol_username` varchar(255) NOT NULL,
    `user_tag` varchar(255) NOT NULL,
    `encrypted_id` varchar(1024) NOT NULL,
    `discord_user` varchar(255) NOT NULL,
    `server_id` varchar(255) NOT NULL,
    `in_game` BOOLEAN NOT NULL,
    `division_solo` varchar(255) NOT NULL,
    `tier_solo` varchar(255) NOT NULL,
    `league_points_solo` int NOT NULL,
    `division_flex` varchar(255) NOT NULL,
    `tier_flex` varchar(255) NOT NULL,
    `league_points_flex` int NOT NULL,
    FOREIGN KEY (`server_id`) REFERENCES `guild_init` (`server_id`)
);