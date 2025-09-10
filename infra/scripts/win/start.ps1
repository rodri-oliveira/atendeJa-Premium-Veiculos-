param(
  [switch]$Dashboards
)

$profileArg = ""
if ($Dashboards) { $profileArg = "--profile dashboards" }

docker compose $profileArg up -d --build
