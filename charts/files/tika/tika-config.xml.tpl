<?xml version="1.0" encoding="UTF-8"?>
<properties>
  <server>
    <params>
      <!-- run each parse in an isolated forked child JVM so that crashes/OOMs
          and taskTimeoutMillis kills cannot affect the main server process -->
      <noFork>false</noFork>
      <!-- maximum time to allow per parse before killing the forked child JVM
          and all subprocesses (e.g. ImageMagick convert) it spawned -->
      <taskTimeoutMillis>{{ .taskTimeoutMillis }}</taskTimeoutMillis>
    </params>
  </server>
  <parsers>

    <parser class="org.apache.tika.parser.DefaultParser">
        <mime-exclude>application/vnd.ms-outlook-pst</mime-exclude>
        <mime-exclude>application/vnd.tcpdump.pcap</mime-exclude>
    </parser>

    <parser class="org.apache.tika.parser.pdf.PDFParser">
      <params>
        <param name="extractInlineImages" type="bool">true</param>
      </params>
    </parser>

    <!-- Do not use the pst parser, we have implemented our own pst extraction
        The default apache tika pst parser does not work very well. -->
    <parser class="org.apache.tika.parser.mbox.OutlookPSTParser">
      <mime-exclude>application/vnd.ms-outlook-pst</mime-exclude>
    </parser>

    <!-- TesseractOCRParser with image preprocessing enabled -->
    <parser class="org.apache.tika.parser.ocr.TesseractOCRParser">
      <params>
        <!-- Enable image preprocessing (requires ImageMagick) -->
        <param name="enableImagePreprocessing" type="bool">true</param>
        <!-- Enable rotation detection (requires Python 3 + scikit-image + numpy) -->
        <param name="applyRotation" type="bool">true</param>
      </params>
    </parser>

  </parsers>
</properties>
