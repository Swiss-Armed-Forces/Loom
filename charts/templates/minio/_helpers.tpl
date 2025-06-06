{{/* vim: set filetype=mustache: */}}

{{/*
Return the appropriate apiVersion for deployment.
*/}}
{{- define "minio.deployment.apiVersion" -}}
  {{- if semverCompare "<1.9-0" .Capabilities.KubeVersion.Version -}}
    {{- print "apps/v1beta2" -}}
  {{- else -}}
    {{- print "apps/v1" -}}
  {{- end -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for statefulset.
*/}}
{{- define "minio.statefulset.apiVersion" -}}
  {{- if semverCompare "<1.16-0" .Capabilities.KubeVersion.Version -}}
    {{- print "apps/v1beta2" -}}
  {{- else -}}
    {{- print "apps/v1" -}}
  {{- end -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for ingress.
*/}}
{{- define "minio.ingress.apiVersion" -}}
  {{- if semverCompare "<1.14-0" .Capabilities.KubeVersion.GitVersion -}}
    {{- print "extensions/v1beta1" -}}
  {{- else if semverCompare "<1.19-0" .Capabilities.KubeVersion.GitVersion -}}
    {{- print "networking.k8s.io/v1beta1" -}}
  {{- else -}}
    {{- print "networking.k8s.io/v1" -}}
  {{- end -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for console ingress.
*/}}
{{- define "minio.consoleIngress.apiVersion" -}}
  {{- if semverCompare "<1.14-0" .Capabilities.KubeVersion.GitVersion -}}
    {{- print "extensions/v1beta1" -}}
  {{- else if semverCompare "<1.19-0" .Capabilities.KubeVersion.GitVersion -}}
    {{- print "networking.k8s.io/v1beta1" -}}
  {{- else -}}
    {{- print "networking.k8s.io/v1" -}}
  {{- end -}}
{{- end -}}

{{/*
Determine secret name.
*/}}
{{- define "minio.secretName" -}}
  {{- if .Values.minio.existingSecret -}}
    {{- .Values.minio.existingSecret }}
  {{- else -}}
    {{- include "app.fullname" . -}}
  {{- end -}}
{{- end -}}

{{/*
Determine domain for hosts
*/}}
{{- define "minio.domain" -}}
  {{- if .Values.minio.domain -}}
    {{- printf ".%s" .Values.minio.domain -}}
  {{- else -}}
    {{- print "" -}}
  {{- end -}}
{{- end -}}

{{/*
Determine name for scc role and rolebinding
*/}}
{{- define "minio.sccRoleName" -}}
  {{- printf "%s-%s" "scc" (include "app.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Properly format optional additional arguments to MinIO binary
*/}}
{{- define "minio.extraArgs" -}}
{{- range .Values.minio.extraArgs -}}
{{ " " }}{{ . }}
{{- end -}}
{{- end -}}

{{/*
Return the proper Docker Image Registry Secret Names
*/}}
{{- define "minio.imagePullSecrets" -}}
{{/*
Helm 2.11 supports the assignment of a value to a variable defined in a different scope,
but Helm 2.9 and 2.10 does not support it, so we need to implement this if-else logic.
Also, we can not use a single if because lazy evaluation is not an option
*/}}
{{- if .Values.minio.global }}
{{- if .Values.minio.global.imagePullSecrets }}
imagePullSecrets:
{{- range .Values.minio.global.imagePullSecrets }}
  - name: {{ . }}
{{- end }}
{{- else if .Values.minio.imagePullSecrets }}
imagePullSecrets:
    {{ toYaml .Values.minio.imagePullSecrets }}
{{- end -}}
{{- else if .Values.minio.imagePullSecrets }}
imagePullSecrets:
    {{ toYaml .Values.minio.imagePullSecrets }}
{{- end -}}
{{- end -}}

{{/*
Formats volumeMount for MinIO TLS keys and trusted certs
*/}}
{{- define "minio.tlsKeysVolumeMount" -}}
{{- if .Values.minio.tls.enabled }}
- name: cert-secret-volume
  mountPath: {{ .Values.minio.certsPath }}
{{- end }}
{{- if or .Values.minio.tls.enabled (ne .Values.minio.trustedCertsSecret "") }}
{{- $casPath := printf "%s/CAs" .Values.minio.certsPath | clean }}
- name: trusted-cert-secret-volume
  mountPath: {{ $casPath }}
{{- end }}
{{- end -}}

{{/*
Formats volume for MinIO TLS keys and trusted certs
*/}}
{{- define "minio.tlsKeysVolume" -}}
{{- if .Values.minio.tls.enabled }}
- name: cert-secret-volume
  secret:
    secretName: {{ tpl .Values.minio.tls.certSecret $ }}
    items:
    - key: {{ .Values.minio.tls.publicCrt }}
      path: public.crt
    - key: {{ .Values.minio.tls.privateKey }}
      path: private.key
{{- end }}
{{- if or .Values.minio.tls.enabled (ne .Values.minio.trustedCertsSecret "") }}
{{- $certSecret := eq .Values.minio.trustedCertsSecret "" | ternary .Values.minio.tls.certSecret .Values.minio.trustedCertsSecret }}
{{- $publicCrt := eq .Values.minio.trustedCertsSecret "" | ternary .Values.minio.tls.publicCrt "" }}
- name: trusted-cert-secret-volume
  secret:
    secretName: {{ $certSecret }}
    {{- if ne $publicCrt "" }}
    items:
    - key: {{ $publicCrt }}
      path: public.crt
    {{- end }}
{{- end }}
{{- end -}}

{{/*
Returns the available value for certain key in an existing secret (if it exists),
otherwise it generates a random value.
*/}}
{{- define "minio.getValueFromSecret" }}
  {{- $len := (default 16 .Length) | int -}}
  {{- $obj := (lookup "v1" "Secret" .Namespace .Name).data -}}
  {{- if $obj }}
    {{- index $obj .Key | b64dec -}}
  {{- else -}}
    {{- randAlphaNum $len -}}
  {{- end -}}
{{- end }}

{{- define "minio.root.username" -}}
  {{- if .Values.minio.rootUser }}
    {{- .Values.minio.rootUser | toString }}
  {{- else }}
    {{- include "minio.getValueFromSecret" (dict "Namespace" .Release.Namespace "Name" (include "app.fullname" .) "Length" 20 "Key" "rootUser") }}
  {{- end }}
{{- end -}}

{{- define "minio.root.password" -}}
  {{- if .Values.minio.rootPassword }}
    {{- .Values.minio.rootPassword | toString }}
  {{- else }}
    {{- include "minio.getValueFromSecret" (dict "Namespace" .Release.Namespace "Name" (include "app.fullname" .) "Length" 40 "Key" "rootPassword") }}
  {{- end }}
{{- end -}}
