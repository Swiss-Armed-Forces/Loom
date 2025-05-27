
{{/*
This template enforces that two specific values in the values.yaml file are equal.
If they are not, Helm will fail with an error during rendering.
This is useful for ensuring consistency between values that must always match,
even when users override them via --set or a custom values file.
*/}}

{{- if ne .Values.domain .Values.minio.domain }}
  {{- fail "domain and minio.domain must be the same" }}
{{- end }}

{{- if ne .Values.image.registry .Values.minio.image.repository }}
  {{- fail "image.registry and minio.image.repository must be the same" }}
{{- end }}

{{- if ne .Values.image.registry .Values.minio.mcImage.repository }}
  {{- fail "image.registry and minio.mcImage.repository must be the same" }}
{{- end }}

{{- if ne .Values.certificate.requireClientCert .Values.minio.certificate.requireClientCert }}
  {{- fail "certificate.requireClientCert and minio.certificate.requireClientCert must be the same" }}
{{- end }}