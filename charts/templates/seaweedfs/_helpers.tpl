{{/*
SeaweedFS component full name
*/}}
{{- define "seaweedfs.fullname" -}}
{{- include "app.fullname" . }}-seaweedfs
{{- end -}}

{{/*
SeaweedFS master peers for cluster formation
*/}}
{{- define "seaweedfs.master.peers" -}}
{{- $replicas := int .Values.seaweedfs.master.replicaCount -}}
{{- $peers := list -}}
{{- range $i := until $replicas -}}
{{- $peers = append $peers (printf "%s-seaweedfs-master-%d.%s-seaweedfs-master:%d" (include "app.fullname" $) $i (include "app.fullname" $) (int $.Values.seaweedfs.master.port)) -}}
{{- end -}}
{{- join "," $peers -}}
{{- end -}}
