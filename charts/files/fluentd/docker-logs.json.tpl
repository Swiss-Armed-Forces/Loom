{
  "index_patterns": [".ds-{{ .Values.fluentd.config.dataStream.name }}-*"],
  "template": {
    "aliases": {},
    "mappings": {},
    "settings": {
      "index": {
        "lifecycle": {
          "name": {{ .Values.fluentd.config.dataStream.ilmName | quote }}
        },
        "routing": {
          "allocation": {
            "include": {
              "_tier_preference": "data_hot"
            }
          }
        },
        "number_of_shards": {{ .Values.fluentd.config.indexTemplate.numberOfShards | quote }},
        "number_of_replicas": {{ .Values.fluentd.config.indexTemplate.numberOfReplicas | quote }}
      }
    }
  }
}
