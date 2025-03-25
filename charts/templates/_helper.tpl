{{/*
Expand the name of the chart.
*/}}
{{- define "app.name" -}}
{{- .Chart.Name | lower -}}
{{- end -}}

{{/*
Create the fullname of the chart.
*/}}
{{- define "app.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "app.name" .) | lower -}}
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
