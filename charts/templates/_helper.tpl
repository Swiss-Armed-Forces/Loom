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
Custom labels for a component
Merges standard labels with global custom labels and component-specific custom labels
Usage: {{ include "app.labels.custom" (dict "context" . "component" "prometheus") }}
*/}}
{{- define "app.labels.custom" -}}
{{- $context := .context -}}
{{- $component := .component -}}
{{- include "app.labels.standard" $context }}
{{- if $context.Values.global }}
{{- if $context.Values.global.customLabels }}
{{- range $key, $value := $context.Values.global.customLabels }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- if $component }}
{{- $componentValues := index $context.Values $component -}}
{{- if $componentValues }}
{{- if $componentValues.customLabels }}
{{- range $key, $value := $componentValues.customLabels }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
Custom annotations for a component
Merges global custom annotations and component-specific custom annotations
Usage: {{ include "app.annotations.custom" (dict "context" . "component" "prometheus") }}
*/}}
{{- define "app.annotations.custom" -}}
{{- $context := .context -}}
{{- $component := .component -}}
{{- if $context.Values.global }}
{{- if $context.Values.global.customAnnotations }}
{{- range $key, $value := $context.Values.global.customAnnotations }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- if $component }}
{{- $componentValues := index $context.Values $component -}}
{{- if $componentValues }}
{{- if $componentValues.customAnnotations }}
{{- range $key, $value := $componentValues.customAnnotations }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
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

{{/*
Custom labels for a PVC from a StatefulSet volumeClaimTemplate.
Only includes user-defined labels (no standard Kubernetes/Helm labels, which are immutable on PVCs).
Accepts either:
  - component: top-level values key (e.g. "elasticsearch") → reads {component}.pvc.customLabels
  - pvcConfig: direct pvc values dict (e.g. .Values.seaweedfs.master.pvc) → reads pvcConfig.customLabels
Usage:
  {{ include "app.pvc.labels.custom" (dict "context" . "component" "elasticsearch") }}
  {{ include "app.pvc.labels.custom" (dict "context" . "pvcConfig" .Values.seaweedfs.master.pvc) }}
*/}}
{{- define "app.pvc.labels.custom" -}}
{{- $context := .context -}}
{{- $component := .component -}}
{{- $pvcConfig := .pvcConfig -}}
{{- if $context.Values.global }}
{{- if $context.Values.global.customPvcLabels }}
{{- range $key, $value := $context.Values.global.customPvcLabels }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- if $component }}
{{- $componentValues := index $context.Values $component -}}
{{- if $componentValues }}
{{- if $componentValues.pvc }}
{{- if $componentValues.pvc.customLabels }}
{{- range $key, $value := $componentValues.pvc.customLabels }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- if $pvcConfig }}
{{- if $pvcConfig.customLabels }}
{{- range $key, $value := $pvcConfig.customLabels }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
Custom annotations for a PVC from a StatefulSet volumeClaimTemplate.
Same usage as app.pvc.labels.custom.
*/}}
{{- define "app.pvc.annotations.custom" -}}
{{- $context := .context -}}
{{- $component := .component -}}
{{- $pvcConfig := .pvcConfig -}}
{{- if $context.Values.global }}
{{- if $context.Values.global.customPvcAnnotations }}
{{- range $key, $value := $context.Values.global.customPvcAnnotations }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- if $component }}
{{- $componentValues := index $context.Values $component -}}
{{- if $componentValues }}
{{- if $componentValues.pvc }}
{{- if $componentValues.pvc.customAnnotations }}
{{- range $key, $value := $componentValues.pvc.customAnnotations }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- if $pvcConfig }}
{{- if $pvcConfig.customAnnotations }}
{{- range $key, $value := $pvcConfig.customAnnotations }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}
{{- end -}}


{{/*
Render envFrom secretRef entries for all enabled ExternalSecrets.
Usage: {{- with include "app.externalSecrets.envFrom" . }}{{ . | nindent 12 }}{{- end }}
*/}}
{{- define "app.externalSecrets.envFrom" -}}
{{- range $secretKey, $secret := .Values.externalSecrets.secrets -}}
{{- if $secret.enabled }}
- secretRef:
    name: {{ $secret.name }}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "cpu-limit-to-count" -}}
  {{/*
  This template converts Kubernetes CPU resource limit to integer CPU count.
  Input can be: millicores (e.g., "500m", "1500m") or whole CPUs (e.g., "2", "2.5")
  Returns minimum of 1 CPU
  */}}
  {{- $cpuLimit := . -}}
  {{- if not (typeIs "string" . ) -}}
    {{- $cpuLimit = toString $cpuLimit -}}
  {{- end -}}
  {{- $cpuCount := 0 -}}
  {{- if hasSuffix "m" $cpuLimit -}}
    {{- /* Handle millicores (e.g., "500m") */ -}}
    {{- $millis := $cpuLimit | trimSuffix "m" | float64 -}}
    {{- $cpuCount = divf $millis 1000 | ceil | int -}}
  {{- else if (mustRegexMatch "^[0-9]+(\\.[0-9]+)?$" $cpuLimit) -}}
    {{- /* Handle whole or decimal CPUs (e.g., "2" or "2.5") */ -}}
    {{- $cpuCount = $cpuLimit | float64 | ceil | int -}}
  {{- else -}}
    {{- printf "\n%s is invalid CPU quantity\nFormat can be: millicores (e.g., 500m) or CPUs (e.g., 2 or 2.5)" $cpuLimit | fail -}}
  {{- end -}}
  {{- /* Ensure minimum of 1 CPU */ -}}
  {{- if lt $cpuCount 1 -}}
    {{- $cpuCount = 1 -}}
  {{- end -}}
  {{- $cpuCount | int64 -}}
{{- end -}}

{{/*
Calculate GOMEMLIMIT from Kubernetes memory limit.
Usage: {{ include "gomemlimit" (dict "memory" "1Gi" "factor" 0.9) }}
Returns: byte value for GOMEMLIMIT (e.g., "966367641")
*/}}
{{- define "gomemlimit" -}}
{{- $memoryBytes := include "SI-to-bytes" .memory | int64 -}}
{{- $factor := .factor | default 0.9 -}}
{{- mulf $memoryBytes $factor | floor | int64 -}}
{{- end -}}
