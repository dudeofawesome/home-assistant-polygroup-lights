api_key="$({
  kubectl exec \
    -n esphome \
    deployments/esphome \
    -- awk \
      '/^api:/{a=1} a&&/key:/{gsub(/.*key: *"?|"?$/ ,""); print; exit}' \
      /config/ir-proxy-hall-bathroom.yaml
})"

case "$api_key" in
  "!secret "*)
    secret_name="${api_key#"!secret "}"
    api_key="$({
      kubectl exec \
        -n esphome \
        deployments/esphome \
        -- awk \
          -v name="$secret_name" \
          '$1 == name ":" {sub(/^[^:]+:[[:space:]]*/, ""); gsub(/^"|"$/, ""); print; exit}' \
          /config/secrets.yaml
    })"
    ;;
esac

cat >"$1" <<EOL
esphome: {name: foo}
esp8266: {board: esp8285}
logger: {}
wifi: { ssid: foo, password: password, min_auth_mode: WPA2 }
api: {encryption: {key: "$api_key"}}
EOL
