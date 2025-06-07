{{/*
Expand the name of the chart.
*/}}
{{- define "app.name" -}}
  {{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" | lower -}}
{{- end -}}

{{/*
Create the fullname of the chart.
*/}}
{{- define "app.fullname" -}}
  {{- printf "%s-%s" .Release.Name (include "app.name" .) | lower -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "app.chart" -}}
  {{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Standard application labels
*/}}
{{- define "app.labels.standard" -}}
app.kubernetes.io/name: {{ .Chart.Name | lower | replace "/" "-" }}
helm.sh/chart: {{ .Chart.Name | lower | replace "/" "-" | replace "+" "_" }}-{{ .Chart.Version | replace "+" "_" | replace "/" "-" }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.Version | replace "+" "_" }}
{{- end -}}

{{/*
Generate a hash suffix based on values to ensure unique job names on configuration changes.

This approach is specifically designed for ArgoCD deployments where using {{ .Release.Revision }}
can cause persistent out-of-sync states. Here's why:

ArgoCD vs Helm Revision Tracking:
- Helm tracks revisions sequentially (1, 2, 3...) for each install/upgrade operation
- ArgoCD renders templates using its own Git-based revision system, not Helm's counter
- This mismatch causes ArgoCD to see different revision numbers than what exists in the cluster
- Result: ArgoCD shows perpetual drift between desired state and live resources

Benefits of Value Hashing:
1. Deterministic: Same values always produce the same hash, ensuring ArgoCD sync consistency
2. Change-sensitive: Hash changes only when actual configuration values change
3. ArgoCD-compatible: No dependency on Helm's revision tracking system
4. Automatic job recreation: New hash triggers job deletion/recreation when config changes
5. Stable when unchanged: Prevents unnecessary job churn when values remain static

This ensures jobs run on every meaningful configuration change while maintaining
ArgoCD's declarative sync model without false drift detection.
*/}}
{{- define "app.valuesHash" -}}
{{- .Values | toYaml | sha256sum | trunc 8 -}}
{{- end -}}


{{- define "SI-to-bytes" -}}
  {{/*
  This template converts the incoming SI value to whole number bytes.
  Input can be: b | B | k | K | m | M | g | G | Ki | Mi | Gi
  Or number without suffix
  */}}
  {{- $si := . -}}
  {{- if not (typeIs "string" . ) -}}
    {{- $si = int64 $si | toString -}}
  {{- end -}}
  {{- $bytes := 0 -}}
  {{- if or (hasSuffix "B" $si) (hasSuffix "b" $si) -}}
    {{- $bytes = $si | trimSuffix "B" | trimSuffix "b" | float64 | floor -}}
  {{- else if or (hasSuffix "K" $si) (hasSuffix "k" $si) -}}
    {{- $raw := $si | trimSuffix "K" | trimSuffix "k" | float64 -}}
    {{- $bytes = mulf $raw (mul 1000) | floor -}}
  {{- else if or (hasSuffix "M" $si) (hasSuffix "m" $si) -}}
    {{- $raw := $si | trimSuffix "M" | trimSuffix "m" | float64 -}}
    {{- $bytes = mulf $raw (mul 1000 1000) | floor -}}
  {{- else if or (hasSuffix "G" $si) (hasSuffix "g" $si) -}}
    {{- $raw := $si | trimSuffix "G" | trimSuffix "g" | float64 -}}
    {{- $bytes = mulf $raw (mul 1000 1000 1000) | floor -}}
  {{- else if hasSuffix "Ki" $si -}}
    {{- $raw := $si | trimSuffix "Ki" | float64 -}}
    {{- $bytes = mulf $raw (mul 1024) | floor -}}
  {{- else if hasSuffix "Mi" $si -}}
    {{- $raw := $si | trimSuffix "Mi" | float64 -}}
    {{- $bytes = mulf $raw (mul 1024 1024) | floor -}}
  {{- else if hasSuffix "Gi" $si -}}
    {{- $raw := $si | trimSuffix "Gi" | float64 -}}
    {{- $bytes = mulf $raw (mul 1024 1024 1024) | floor -}}
  {{- else if (mustRegexMatch "^[0-9]+$" $si) -}}
    {{- $bytes = $si -}}
  {{- else -}}
    {{- printf "\n%s is invalid SI quantity\nSuffixes can be: b | B | k | K | m | M | g | G | Ki | Mi | Gi or without any Suffixes" $si | fail -}}
  {{- end -}}
  {{- $bytes | int64 -}}
{{- end -}}
