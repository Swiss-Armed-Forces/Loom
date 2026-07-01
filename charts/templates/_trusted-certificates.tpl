{{/*
Init container that installs trusted CA certificates into a shared emptyDir volume.
Only rendered when .Values.trustedCertificates.certs is non-empty.
Usage: {{- with include "app.trustedCerts.initContainer" . }}{{ . | nindent 8 }}{{- end }}
*/}}
{{- define "app.trustedCerts.initContainer" -}}
{{- if .Values.trustedCertificates.certs }}
- name: ca-installer
  image: {{ .Values.image.registry }}/{{ .Values.trustedCertificates.initContainer.image.repository }}:{{ default (default .Chart.AppVersion .Values.image.tag) .Values.trustedCertificates.initContainer.image.tag }}
  imagePullPolicy: {{ .Values.image.pullPolicy }}
  command:
    - sh
    - -c
    - |
      set -eu
      cp /etc/ssl/certs/ca-certificates.crt /ca-bundle/ca-certificates.crt
      for cert in /ca-certificates-configmap/*.crt; do
        cat "$cert" >> /ca-bundle/ca-certificates.crt
      done
  volumeMounts:
    - name: ca-certificates-configmap
      mountPath: /ca-certificates-configmap
      readOnly: true
    - name: ca-bundle
      mountPath: /ca-bundle
  {{- if .Values.trustedCertificates.initContainer.resources }}
  resources: {{- toYaml .Values.trustedCertificates.initContainer.resources | nindent 4 }}
  {{- end }}
{{- end }}
{{- end -}}

{{/*
Volumes for the trusted CA certificates init container pattern.
Only rendered when .Values.trustedCertificates.certs is non-empty.
Usage: {{- with include "app.trustedCerts.volumes" . }}{{ . | nindent 8 }}{{- end }}
*/}}
{{- define "app.trustedCerts.volumes" -}}
{{- if .Values.trustedCertificates.certs }}
- name: ca-certificates-configmap
  configMap:
    name: {{ include "app.fullname" . }}-trusted-certificates
- name: ca-bundle
  emptyDir: {}
{{- end }}
{{- end -}}

{{/*
VolumeMount for the trusted CA bundle in main containers.
Only rendered when .Values.trustedCertificates.certs is non-empty.
Usage: {{- with include "app.trustedCerts.volumeMount" . }}{{ . | nindent 12 }}{{- end }}
*/}}
{{- define "app.trustedCerts.volumeMount" -}}
{{- if .Values.trustedCertificates.certs }}
- name: ca-bundle
  mountPath: /etc/ssl/certs/ca-certificates.crt
  subPath: ca-certificates.crt
{{- end }}
{{- end -}}

{{/*
Environment variables that point Python and Node.js at the trusted CA bundle.
Only rendered when .Values.trustedCertificates.certs is non-empty.
Usage: {{- with include "app.trustedCerts.env" . }}{{ . | nindent 12 }}{{- end }}
*/}}
{{- define "app.trustedCerts.env" -}}
{{- if .Values.trustedCertificates.certs }}
- name: SSL_CERT_FILE
  value: /etc/ssl/certs/ca-certificates.crt
- name: REQUESTS_CA_BUNDLE
  value: /etc/ssl/certs/ca-certificates.crt
- name: NODE_EXTRA_CA_CERTS
  value: /etc/ssl/certs/ca-certificates.crt
{{- end }}
{{- end -}}
