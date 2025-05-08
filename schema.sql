/* Uses mariadb */
CREATE TABLE invites (
  invitee BIGINT UNSIGNED NOT NULL,
  inviter BIGINT UNSIGNED NOT NULL,
  server BIGINT UNSIGNED NOT NULL,
  time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unique_server_invitee (server, invitee)
);

