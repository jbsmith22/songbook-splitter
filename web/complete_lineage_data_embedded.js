const LINEAGE_DATA = {
  "generated": "2026-02-06",
  "summary": {
    "total_books": 126,
    "with_verified_songs": 126,
    "with_output_files": 126,
    "with_local_manifest": 119,
    "exact_matches": 100
  },
  "books": [
    {
      "book_id": "v2-00171fce4db3bdf9-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 16,
        "output_files": 16,
        "local_pdfs": 16
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/ACDC/ACDC - Anthology.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "ACDC",
          "book_name": "Anthology",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/ACDC/ACDC - Anthology.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 143,
              "errors": 51,
              "error_rate": 35.7
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 16
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 16
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 16
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "ACDC\\ACDC - Anthology",
          "pdf_count": 16,
          "total_songs": 16
        },
        "7_local_pdfs": {
          "count": 16
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 16
        }
      },
      "page_analysis_error_rate": 35.66433566433567,
      "local_folder": "ACDC\\ACDC - Anthology"
    },
    {
      "book_id": "v2-035d688e731b88c1-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 40,
        "output_files": 40,
        "local_pdfs": 40
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Burt Bacharach/Burt Bacharach - 40 Golden Songs Of.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Burt Bacharach",
          "book_name": "40 Golden Songs Of",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Burt Bacharach/Burt Bacharach - 40 Golden Songs Of.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 63,
              "errors": 19,
              "error_rate": 30.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 40
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 40
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 41
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Burt Bacharach\\Burt Bacharach - 40 Golden Songs Of",
          "pdf_count": 40,
          "total_songs": 40
        },
        "7_local_pdfs": {
          "count": 40
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 30.158730158730158,
      "local_folder": "Burt Bacharach\\Burt Bacharach - 40 Golden Songs Of"
    },
    {
      "book_id": "v2-04f34885c435fac6-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 26,
        "output_files": 26,
        "local_pdfs": 26
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Cream/Cream - Cream Complete.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Cream",
          "book_name": "Cream Complete",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Cream/Cream - Cream Complete.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 70,
              "errors": 33,
              "error_rate": 47.1
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 26
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 26
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 26
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Cream\\Cream - Cream Complete",
          "pdf_count": 26,
          "total_songs": 26
        },
        "7_local_pdfs": {
          "count": 26
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 47.14285714285714,
      "local_folder": "Cream\\Cream - Cream Complete"
    },
    {
      "book_id": "v2-09a39b6d0883b0a5-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 17,
        "output_files": 17,
        "local_pdfs": 17
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bruce Springsteen/Bruce Springsteen - Greatest Hits.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bruce Springsteen",
          "book_name": "Greatest Hits",
          "songs_extracted": 17,
          "source_pdf_uri": "s3://jsmith-input/Bruce Springsteen/Bruce Springsteen - Greatest Hits.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 75,
              "errors": 22,
              "error_rate": 29.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 17
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 17
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 17
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bruce Springsteen\\Bruce Springsteen - Greatest Hits",
          "pdf_count": 17,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 17
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 17
        }
      },
      "page_analysis_error_rate": 29.333333333333332,
      "local_folder": "Bruce Springsteen\\Bruce Springsteen - Greatest Hits"
    },
    {
      "book_id": "v2-0bc6711df3576875-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 4,
        "output_files": 4,
        "local_pdfs": 4
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Seger/Bob Seger - Greatest Hits.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Seger",
          "book_name": "Greatest Hits",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Seger/Bob Seger - Greatest Hits.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 79,
              "errors": 57,
              "error_rate": 72.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 4
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 4
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 7
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Seger\\Bob Seger - Greatest Hits",
          "pdf_count": 4,
          "total_songs": 4
        },
        "7_local_pdfs": {
          "count": 4
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 72.15189873417721,
      "local_folder": "Bob Seger\\Bob Seger - Greatest Hits"
    },
    {
      "book_id": "v2-0d4afc464d31f666-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 19,
        "output_files": 19,
        "local_pdfs": 19
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Best Of Piano Solos.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Best Of Piano Solos",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Best Of Piano Solos.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 78,
              "errors": 46,
              "error_rate": 59.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 19
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 19
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 19
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Best Of Piano Solos",
          "pdf_count": 19,
          "total_songs": 19
        },
        "7_local_pdfs": {
          "count": 19
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 19
        }
      },
      "page_analysis_error_rate": 58.97435897435898,
      "local_folder": "Billy Joel\\Billy Joel - Best Of Piano Solos"
    },
    {
      "book_id": "v2-10c9b38769bc4333-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 54,
        "output_files": 54,
        "local_pdfs": 54
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Barry Manilow/Barry Manilow - Anthology.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Barry Manilow",
          "book_name": "Anthology",
          "songs_extracted": 54,
          "source_pdf_uri": "s3://jsmith-input/Barry Manilow/Barry Manilow - Anthology.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 321,
              "errors": 25,
              "error_rate": 7.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 54
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 54
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 54
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Barry Manilow\\Barry Manilow - Anthology",
          "pdf_count": 54,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 54
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 54
        }
      },
      "page_analysis_error_rate": 7.78816199376947,
      "local_folder": "Barry Manilow\\Barry Manilow - Anthology"
    },
    {
      "book_id": "v2-11e0fa71720dd8c5-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 3,
        "output_files": 3,
        "local_pdfs": 3
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carole King/Carole King - Youre The Voice.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carole King",
          "book_name": "Youre The Voice",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carole King/Carole King - Youre The Voice.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 51,
              "errors": 39,
              "error_rate": 76.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 3
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 3
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 3
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carole King\\Carole King - Youre The Voice",
          "pdf_count": 3,
          "total_songs": 3
        },
        "7_local_pdfs": {
          "count": 3
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 76.47058823529412,
      "local_folder": "Carole King\\Carole King - Youre The Voice"
    },
    {
      "book_id": "v2-15ee87f6c6352495-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 9,
        "output_files": 9,
        "local_pdfs": 9
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Greatest Hits Vol III.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Greatest Hits Vol III",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Greatest Hits Vol III.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 85,
              "errors": 14,
              "error_rate": 16.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 9
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 9
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 10
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Greatest Hits Vol III",
          "pdf_count": 9,
          "total_songs": 9
        },
        "7_local_pdfs": {
          "count": 9
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 9
        }
      },
      "page_analysis_error_rate": 16.470588235294116,
      "local_folder": "Billy Joel\\Billy Joel - Greatest Hits Vol III"
    },
    {
      "book_id": "v2-1602c5f5f8f2ed15-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 38,
        "output_files": 38,
        "local_pdfs": 38
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Cole Porter/Cole Porter - The Very Best Of Cole Porter.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Cole Porter",
          "book_name": "The Very Best Of Cole Porter",
          "songs_extracted": 38,
          "source_pdf_uri": "s3://jsmith-input/Cole Porter/Cole Porter - The Very Best Of Cole Porter.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 162,
              "errors": 30,
              "error_rate": 18.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 38
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 38
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 38
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Cole Porter\\Cole Porter - The Very Best Of Cole Porter",
          "pdf_count": 38,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 38
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 38
        }
      },
      "page_analysis_error_rate": 18.51851851851852,
      "local_folder": "Cole Porter\\Cole Porter - The Very Best Of Cole Porter"
    },
    {
      "book_id": "v2-170195b568600092-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 121,
        "output_files": 121,
        "local_pdfs": 121
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Burl Ives/Burl Ives - Song Book.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Burl Ives",
          "book_name": "Song Book",
          "songs_extracted": 121,
          "source_pdf_uri": "s3://jsmith-input/Burl Ives/Burl Ives - Song Book.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 285,
              "errors": 24,
              "error_rate": 8.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 121
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 121
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 121
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Burl Ives\\Burl Ives - Song Book",
          "pdf_count": 121,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 121
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 121
        }
      },
      "page_analysis_error_rate": 8.421052631578947,
      "local_folder": "Burl Ives\\Burl Ives - Song Book"
    },
    {
      "book_id": "v2-17b5c442898cdbde-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 16,
        "output_files": 16,
        "local_pdfs": 17
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Ben Folds/Ben Folds Five - Selections From Naked Baby Photos _Score_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Ben Folds",
          "book_name": "Selections From Naked Baby Photos _Score_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Ben Folds/Ben Folds Five - Selections From Naked Baby Photos _Score_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 143,
              "errors": 76,
              "error_rate": 53.1
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 16
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 16
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 16
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Ben Folds\\Ben Folds - Selections From Naked Baby Photos _Score_",
          "pdf_count": 17,
          "total_songs": 16
        },
        "7_local_pdfs": {
          "count": 17
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 17
        }
      },
      "page_analysis_error_rate": 53.14685314685315,
      "local_folder": "Ben Folds\\Ben Folds - Selections From Naked Baby Photos _Score_"
    },
    {
      "book_id": "v2-1c8594e8f5042abd-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 13,
        "output_files": 13,
        "local_pdfs": 13
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carole King/Carole King - Bradleys Best Of The Best _Organ_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carole King",
          "book_name": "Bradleys Best Of The Best _Organ_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carole King/Carole King - Bradleys Best Of The Best _Organ_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 40,
              "errors": 19,
              "error_rate": 47.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 13
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 13
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 14
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carole King\\Carole King - Bradleys Best Of The Best _Organ_",
          "pdf_count": 13,
          "total_songs": 13
        },
        "7_local_pdfs": {
          "count": 13
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 47.5,
      "local_folder": "Carole King\\Carole King - Bradleys Best Of The Best _Organ_"
    },
    {
      "book_id": "v2-1dd1de739b28d94b-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 28,
        "output_files": 28,
        "local_pdfs": 28
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Songbook.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Songbook",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Songbook.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 124,
              "errors": 72,
              "error_rate": 58.1
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 28
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 28
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 36
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Songbook",
          "pdf_count": 28,
          "total_songs": 28
        },
        "7_local_pdfs": {
          "count": 28
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 58.06451612903226,
      "local_folder": "Bob Dylan\\Bob Dylan - Songbook"
    },
    {
      "book_id": "v2-1e46e821cacf170d-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 209,
        "output_files": 209,
        "local_pdfs": 209
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - All Songs 1962-1974.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "All Songs 1962-1974",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - All Songs 1962-1974.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 289,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 209
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 209
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 211
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - All Songs 1962-1974",
          "pdf_count": 209,
          "total_songs": 209
        },
        "7_local_pdfs": {
          "count": 209
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 209
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Beatles\\Beatles - All Songs 1962-1974"
    },
    {
      "book_id": "v2-202427d81f7dc861-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 10,
        "output_files": 10,
        "local_pdfs": 9
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bruce Springsteen/Bruce Springsteen - Lucky Town.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bruce Springsteen",
          "book_name": "Lucky Town",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bruce Springsteen/Bruce Springsteen - Lucky Town.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 38,
              "errors": 26,
              "error_rate": 68.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 10
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 10
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 10
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bruce Springsteen\\Bruce Springsteen - Lucky Town",
          "pdf_count": 9,
          "total_songs": 10
        },
        "7_local_pdfs": {
          "count": 9
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 68.42105263157895,
      "local_folder": "Bruce Springsteen\\Bruce Springsteen - Lucky Town"
    },
    {
      "book_id": "v2-21757ed1d865a6d4-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 29,
        "output_files": 29,
        "local_pdfs": 29
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Anthology.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Anthology",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Anthology.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 176,
              "errors": 88,
              "error_rate": 50.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 29
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 29
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 29
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Anthology",
          "pdf_count": 29,
          "total_songs": 29
        },
        "7_local_pdfs": {
          "count": 29
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 29
        }
      },
      "page_analysis_error_rate": 50.0,
      "local_folder": "Billy Joel\\Billy Joel - Anthology"
    },
    {
      "book_id": "v2-2268c018c8a6ae2a-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 13,
        "output_files": 13,
        "local_pdfs": 13
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Nashville Skyline.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Nashville Skyline",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Nashville Skyline.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 51,
              "errors": 28,
              "error_rate": 54.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 13
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 13
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 13
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Nashville Skyline",
          "pdf_count": 13,
          "total_songs": 13
        },
        "7_local_pdfs": {
          "count": 13
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 54.90196078431373,
      "local_folder": "Bob Dylan\\Bob Dylan - Nashville Skyline"
    },
    {
      "book_id": "v2-283c53469d04aa45-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 35,
        "output_files": 35,
        "local_pdfs": 35
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carole King/Carole King - Classics.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carole King",
          "book_name": "Classics",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carole King/Carole King - Classics.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 76,
              "errors": 44,
              "error_rate": 57.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 35
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 35
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 35
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carole King\\Carole King - Classics",
          "pdf_count": 35,
          "total_songs": 35
        },
        "7_local_pdfs": {
          "count": 35
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 57.89473684210527,
      "local_folder": "Carole King\\Carole King - Classics"
    },
    {
      "book_id": "v2-28dc34c7edb23410-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 26,
        "output_files": 26,
        "local_pdfs": 26
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Anthology 3 page_01_-_36.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Anthology 3 page_01_-_36",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Anthology 3 page_01_-_36.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 35,
              "errors": 21,
              "error_rate": 60.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 26
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 26
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 26
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Anthology 3 page_01_-_36",
          "pdf_count": 26,
          "total_songs": 26
        },
        "7_local_pdfs": {
          "count": 26
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 26
        }
      },
      "page_analysis_error_rate": 60.0,
      "local_folder": "Beatles\\Beatles - Anthology 3 page_01_-_36"
    },
    {
      "book_id": "v2-2a5da4c41bcff603-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 4,
        "output_files": 4,
        "local_pdfs": 4
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Sergeant Peppers Lonely Hearts Club Band.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Sergeant Peppers Lonely Hearts Club Band",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Sergeant Peppers Lonely Hearts Club Band.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 56,
              "errors": 40,
              "error_rate": 71.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 4
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 4
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 5
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Sergeant Peppers Lonely Hearts Club Band",
          "pdf_count": 4,
          "total_songs": 4
        },
        "7_local_pdfs": {
          "count": 4
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 4
        }
      },
      "page_analysis_error_rate": 71.42857142857143,
      "local_folder": "Beatles\\Beatles - Sergeant Peppers Lonely Hearts Club Band"
    },
    {
      "book_id": "v2-2d6f17e729bd84e0-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 14,
        "output_files": 14,
        "local_pdfs": 11
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bee Gees/Bee Gees - Anthology.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bee Gees",
          "book_name": "Anthology",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bee Gees/Bee Gees - Anthology.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 133,
              "errors": 88,
              "error_rate": 66.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 14
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 14
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 18
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bee Gees\\Bee Gees - Anthology",
          "pdf_count": 11,
          "total_songs": 14
        },
        "7_local_pdfs": {
          "count": 11
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 11
        }
      },
      "page_analysis_error_rate": 66.16541353383458,
      "local_folder": "Bee Gees\\Bee Gees - Anthology"
    },
    {
      "book_id": "v2-2ee350558576c62f-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 2,
        "output_files": 2,
        "local_pdfs": 1
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Anthology 2 page_73_-112.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Anthology 2 page_73_-112",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Anthology 2 page_73_-112.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 39,
              "errors": 31,
              "error_rate": 79.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 2
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 2
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 2
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Anthology 2 page_73_-112",
          "pdf_count": 1,
          "total_songs": 2
        },
        "7_local_pdfs": {
          "count": 1
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 1
        }
      },
      "page_analysis_error_rate": 79.48717948717949,
      "local_folder": "Beatles\\Beatles - Anthology 2 page_73_-112"
    },
    {
      "book_id": "v2-30bac5d53fcb7d40-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 46,
        "output_files": 46,
        "local_pdfs": 46
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Anthology 1.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Anthology 1",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Anthology 1.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 193,
              "errors": 89,
              "error_rate": 46.1
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 46
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 46
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 47
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Anthology 1",
          "pdf_count": 46,
          "total_songs": 46
        },
        "7_local_pdfs": {
          "count": 46
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 46.1139896373057,
      "local_folder": "Bob Dylan\\Bob Dylan - Anthology 1"
    },
    {
      "book_id": "v2-383f2d3cfb36dbf7-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 7,
        "output_files": 7,
        "local_pdfs": 7
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Avril Lavigne/Avril Lavigne - The Best Damn Thing _PVG Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Avril Lavigne",
          "book_name": "The Best Damn Thing _PVG Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Avril Lavigne/Avril Lavigne - The Best Damn Thing _PVG Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 93,
              "errors": 65,
              "error_rate": 69.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 7
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 7
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 9
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Avril Lavigne\\Avril Lavigne - The Best Damn Thing _PVG Book_",
          "pdf_count": 7,
          "total_songs": 7
        },
        "7_local_pdfs": {
          "count": 7
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 7
        }
      },
      "page_analysis_error_rate": 69.89247311827957,
      "local_folder": "Avril Lavigne\\Avril Lavigne - The Best Damn Thing _PVG Book_"
    },
    {
      "book_id": "v2-3906e27e01893f40-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 8,
        "output_files": 8,
        "local_pdfs": 8
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Rock Score.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Rock Score",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Rock Score.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 76,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 8
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 8
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 8
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Rock Score",
          "pdf_count": 8,
          "total_songs": 8
        },
        "7_local_pdfs": {
          "count": 8
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 8
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Billy Joel\\Billy Joel - Rock Score"
    },
    {
      "book_id": "v2-39473d0cea697346-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 43,
        "output_files": 43,
        "local_pdfs": 43
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carpenters/Carpenters - Anthology.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carpenters",
          "book_name": "Anthology",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carpenters/Carpenters - Anthology.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 232,
              "errors": 79,
              "error_rate": 34.1
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 43
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 43
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 43
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carpenters\\Carpenters - Anthology",
          "pdf_count": 43,
          "total_songs": 43
        },
        "7_local_pdfs": {
          "count": 43
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 34.05172413793103,
      "local_folder": "Carpenters\\Carpenters - Anthology"
    },
    {
      "book_id": "v2-398106b6f05d4207-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 20,
        "output_files": 20,
        "local_pdfs": 20
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Anthology 1.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Anthology 1",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Anthology 1.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 82,
              "errors": 33,
              "error_rate": 40.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 20
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 20
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 21
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Anthology 1",
          "pdf_count": 20,
          "total_songs": 20
        },
        "7_local_pdfs": {
          "count": 20
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 20
        }
      },
      "page_analysis_error_rate": 40.243902439024396,
      "local_folder": "Beatles\\Beatles - Anthology 1"
    },
    {
      "book_id": "v2-39ff5ee37e4ea31f-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 27,
        "output_files": 27,
        "local_pdfs": 27
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Buddy Holly/Buddy Holly - Golden Anniversary Songbook.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Buddy Holly",
          "book_name": "Golden Anniversary Songbook",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Buddy Holly/Buddy Holly - Golden Anniversary Songbook.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 114,
              "errors": 62,
              "error_rate": 54.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 27
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 27
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 27
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Buddy Holly\\Buddy Holly - Golden Anniversary Songbook",
          "pdf_count": 27,
          "total_songs": 27
        },
        "7_local_pdfs": {
          "count": 27
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 54.385964912280706,
      "local_folder": "Buddy Holly\\Buddy Holly - Golden Anniversary Songbook"
    },
    {
      "book_id": "v2-3c74363f9720af04-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 8,
        "output_files": 8,
        "local_pdfs": 8
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carole King/Carole King - Keyboard Play-Along Vol 22.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carole King",
          "book_name": "Keyboard Play-Along Vol 22",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carole King/Carole King - Keyboard Play-Along Vol 22.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 63,
              "errors": 39,
              "error_rate": 61.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 8
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 8
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 8
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carole King\\Carole King - Keyboard Play-Along Vol 22",
          "pdf_count": 8,
          "total_songs": 8
        },
        "7_local_pdfs": {
          "count": 8
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 61.904761904761905,
      "local_folder": "Carole King\\Carole King - Keyboard Play-Along Vol 22"
    },
    {
      "book_id": "v2-3d6470dcb9339188-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 13,
        "output_files": 13,
        "local_pdfs": 13
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bruce Springsteen/Bruce Springsteen - Born In The USA.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bruce Springsteen",
          "book_name": "Born In The USA",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bruce Springsteen/Bruce Springsteen - Born In The USA.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 71,
              "errors": 47,
              "error_rate": 66.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 13
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 13
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 13
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bruce Springsteen\\Bruce Springsteen - Born In The USA",
          "pdf_count": 13,
          "total_songs": 13
        },
        "7_local_pdfs": {
          "count": 13
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 66.19718309859155,
      "local_folder": "Bruce Springsteen\\Bruce Springsteen - Born In The USA"
    },
    {
      "book_id": "v2-404b4a9fbaf70922-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 6,
        "output_files": 6,
        "local_pdfs": 6
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Rock Score.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Rock Score",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Rock Score.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 81,
              "errors": 58,
              "error_rate": 71.6
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 6
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 6
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 6
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Rock Score",
          "pdf_count": 6,
          "total_songs": 6
        },
        "7_local_pdfs": {
          "count": 6
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 71.60493827160494,
      "local_folder": "Bob Dylan\\Bob Dylan - Rock Score"
    },
    {
      "book_id": "v2-40ea87a721820a15-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 13,
        "output_files": 13,
        "local_pdfs": 13
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/America/America - Greatest Hits.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "America",
          "book_name": "Greatest Hits",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/America/America - Greatest Hits.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 59,
              "errors": 40,
              "error_rate": 67.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 13
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 13
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 13
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "America\\America - Greatest Hits",
          "pdf_count": 13,
          "total_songs": 13
        },
        "7_local_pdfs": {
          "count": 13
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 13
        }
      },
      "page_analysis_error_rate": 67.79661016949152,
      "local_folder": "America\\America - Greatest Hits"
    },
    {
      "book_id": "v2-419995ff8edb29d6-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 47,
        "output_files": 47,
        "local_pdfs": 47
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Complete Vol 1.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Complete Vol 1",
          "songs_extracted": 47,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Complete Vol 1.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 258,
              "errors": 21,
              "error_rate": 8.1
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 47
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 47
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 47
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Complete Vol 1",
          "pdf_count": 47,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 47
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 47
        }
      },
      "page_analysis_error_rate": 8.13953488372093,
      "local_folder": "Billy Joel\\Billy Joel - Complete Vol 1"
    },
    {
      "book_id": "v2-437391d051019961-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 6,
        "output_files": 6,
        "local_pdfs": 7
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Ben Folds/Ben Folds Five - Rockin The Suburbs.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Ben Folds",
          "book_name": "Rockin The Suburbs",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Ben Folds/Ben Folds Five - Rockin The Suburbs.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 86,
              "errors": 54,
              "error_rate": 62.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 6
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 6
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 8
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Ben Folds\\Ben Folds - Rockin The Suburbs",
          "pdf_count": 7,
          "total_songs": 6
        },
        "7_local_pdfs": {
          "count": 7
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 7
        }
      },
      "page_analysis_error_rate": 62.7906976744186,
      "local_folder": "Ben Folds\\Ben Folds - Rockin The Suburbs"
    },
    {
      "book_id": "v2-43a6b853b3c04301-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 9,
        "output_files": 9,
        "local_pdfs": 9
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Turnstiles.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Turnstiles",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Turnstiles.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 51,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 9
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 9
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 9
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Turnstiles",
          "pdf_count": 9,
          "total_songs": 9
        },
        "7_local_pdfs": {
          "count": 9
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 9
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Billy Joel\\Billy Joel - Turnstiles"
    },
    {
      "book_id": "v2-44b29a17fd109bc2-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 5,
        "output_files": 5,
        "local_pdfs": 5
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Belinda Carlisle/Belinda Carlisle - 5 Of The Best _PVG_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Belinda Carlisle",
          "book_name": "5 Of The Best _PVG_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Belinda Carlisle/Belinda Carlisle - 5 Of The Best _PVG_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 32,
              "errors": 19,
              "error_rate": 59.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 5
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 5
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 5
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Belinda Carlisle\\Belinda Carlisle - 5 Of The Best _PVG_",
          "pdf_count": 5,
          "total_songs": 5
        },
        "7_local_pdfs": {
          "count": 5
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 5
        }
      },
      "page_analysis_error_rate": 59.375,
      "local_folder": "Belinda Carlisle\\Belinda Carlisle - 5 Of The Best _PVG_"
    },
    {
      "book_id": "v2-4867fd1afeae8db3-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 13,
        "output_files": 13,
        "local_pdfs": 12
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carole King/Carole King - Tapestry.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carole King",
          "book_name": "Tapestry",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carole King/Carole King - Tapestry.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 72,
              "errors": 46,
              "error_rate": 63.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 13
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 13
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 12
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carole King\\Carole King - Tapestry",
          "pdf_count": 12,
          "total_songs": 13
        },
        "7_local_pdfs": {
          "count": 12
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 63.888888888888886,
      "local_folder": "Carole King\\Carole King - Tapestry"
    },
    {
      "book_id": "v2-4d44d704e2722571-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 12,
        "output_files": 12,
        "local_pdfs": 12
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Live At The Hollywood Bowl _2_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Live At The Hollywood Bowl _2_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Live At The Hollywood Bowl _2_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 36,
              "errors": 21,
              "error_rate": 58.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 12
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 12
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 12
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Live At The Hollywood Bowl _2_",
          "pdf_count": 12,
          "total_songs": 12
        },
        "7_local_pdfs": {
          "count": 12
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 12
        }
      },
      "page_analysis_error_rate": 58.333333333333336,
      "local_folder": "Beatles\\Beatles - Live At The Hollywood Bowl _2_"
    },
    {
      "book_id": "v2-504918da8c736ac3-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 93,
        "output_files": 93,
        "local_pdfs": 93
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Essential Songs.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Essential Songs",
          "songs_extracted": 93,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Essential Songs.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 401,
              "errors": 25,
              "error_rate": 6.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 93
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 93
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 93
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Essential Songs",
          "pdf_count": 93,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 93
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 93
        }
      },
      "page_analysis_error_rate": 6.234413965087282,
      "local_folder": "Beatles\\Beatles - Essential Songs"
    },
    {
      "book_id": "v2-5306a68545b7d1b3-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 9,
        "output_files": 9,
        "local_pdfs": 9
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Desire.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Desire",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Desire.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 41,
              "errors": 21,
              "error_rate": 51.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 9
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 9
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 9
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Desire",
          "pdf_count": 9,
          "total_songs": 9
        },
        "7_local_pdfs": {
          "count": 9
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 51.21951219512195,
      "local_folder": "Bob Dylan\\Bob Dylan - Desire"
    },
    {
      "book_id": "v2-5326323586fb431b-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 35,
        "output_files": 35,
        "local_pdfs": 35
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carole King/Carole King - Classics _2_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carole King",
          "book_name": "Classics _2_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carole King/Carole King - Classics _2_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 128,
              "errors": 66,
              "error_rate": 51.6
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 35
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 35
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 35
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carole King\\Carole King - Classics _2_",
          "pdf_count": 35,
          "total_songs": 35
        },
        "7_local_pdfs": {
          "count": 35
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 51.5625,
      "local_folder": "Carole King\\Carole King - Classics _2_"
    },
    {
      "book_id": "v2-54984706b2548c5b-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 179,
        "output_files": 179,
        "local_pdfs": 179
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Complete Scores.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Complete Scores",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Complete Scores.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 1121,
              "errors": 194,
              "error_rate": 17.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 179
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 179
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 179
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Complete Scores",
          "pdf_count": 179,
          "total_songs": 179
        },
        "7_local_pdfs": {
          "count": 179
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 179
        }
      },
      "page_analysis_error_rate": 17.305976806422837,
      "local_folder": "Beatles\\Beatles - Complete Scores"
    },
    {
      "book_id": "v2-572ab40c580d53b6-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 209,
        "output_files": 209,
        "local_pdfs": 209
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Songbook.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Songbook",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Songbook.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 289,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 209
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 209
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 212
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Songbook",
          "pdf_count": 209,
          "total_songs": 209
        },
        "7_local_pdfs": {
          "count": 209
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 209
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Beatles\\Beatles - Songbook"
    },
    {
      "book_id": "v2-5ce5c28cd90427a2-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 12,
        "output_files": 12,
        "local_pdfs": 12
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carpenters/Carpenters - Note For Note.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carpenters",
          "book_name": "Note For Note",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carpenters/Carpenters - Note For Note.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 80,
              "errors": 49,
              "error_rate": 61.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 12
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 12
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 12
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carpenters\\Carpenters - Note For Note",
          "pdf_count": 12,
          "total_songs": 12
        },
        "7_local_pdfs": {
          "count": 12
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 61.25000000000001,
      "local_folder": "Carpenters\\Carpenters - Note For Note"
    },
    {
      "book_id": "v2-5d1865eda76ebdd0-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 14,
        "output_files": 14,
        "local_pdfs": 14
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Burt Bacharach/Burt Bacharach - Bacharach Collection.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Burt Bacharach",
          "book_name": "Bacharach Collection",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Burt Bacharach/Burt Bacharach - Bacharach Collection.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 42,
              "errors": 20,
              "error_rate": 47.6
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 14
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 14
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 15
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Burt Bacharach\\Burt Bacharach - Bacharach Collection",
          "pdf_count": 14,
          "total_songs": 14
        },
        "7_local_pdfs": {
          "count": 14
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 47.61904761904761,
      "local_folder": "Burt Bacharach\\Burt Bacharach - Bacharach Collection"
    },
    {
      "book_id": "v2-5e55637b45ed67e5-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 8,
        "output_files": 8,
        "local_pdfs": 8
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bruce Springsteen/Bruce Springsteen - Born To Run.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bruce Springsteen",
          "book_name": "Born To Run",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bruce Springsteen/Bruce Springsteen - Born To Run.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 92,
              "errors": 56,
              "error_rate": 60.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 8
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 8
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 8
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bruce Springsteen\\Bruce Springsteen - Born To Run",
          "pdf_count": 8,
          "total_songs": 8
        },
        "7_local_pdfs": {
          "count": 8
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 60.86956521739131,
      "local_folder": "Bruce Springsteen\\Bruce Springsteen - Born To Run"
    },
    {
      "book_id": "v2-5e5d9caa55d84136-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 4,
        "output_files": 4,
        "local_pdfs": 4
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Rubber Soul.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Rubber Soul",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Rubber Soul.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 51,
              "errors": 39,
              "error_rate": 76.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 4
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 4
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 5
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Rubber Soul",
          "pdf_count": 4,
          "total_songs": 4
        },
        "7_local_pdfs": {
          "count": 4
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 4
        }
      },
      "page_analysis_error_rate": 76.47058823529412,
      "local_folder": "Beatles\\Beatles - Rubber Soul"
    },
    {
      "book_id": "v2-60854716b34d4cce-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 22,
        "output_files": 22,
        "local_pdfs": 22
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carpenters/Carpenters - Love Songs.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carpenters",
          "book_name": "Love Songs",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carpenters/Carpenters - Love Songs.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 108,
              "errors": 55,
              "error_rate": 50.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 22
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 22
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 22
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carpenters\\Carpenters - Love Songs",
          "pdf_count": 22,
          "total_songs": 22
        },
        "7_local_pdfs": {
          "count": 22
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 50.92592592592593,
      "local_folder": "Carpenters\\Carpenters - Love Songs"
    },
    {
      "book_id": "v2-6138f422e856af59-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 15,
        "output_files": 15,
        "local_pdfs": 14
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Blues Brothers/Blues Brothers - Complete.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Blues Brothers",
          "book_name": "Complete",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Blues Brothers/Blues Brothers - Complete.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 76,
              "errors": 39,
              "error_rate": 51.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 15
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 15
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 14
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Blues Brothers\\Blues Brothers - Complete",
          "pdf_count": 14,
          "total_songs": 15
        },
        "7_local_pdfs": {
          "count": 14
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 51.31578947368421,
      "local_folder": "Blues Brothers\\Blues Brothers - Complete"
    },
    {
      "book_id": "v2-62fb6deda3ec80d1-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 13,
        "output_files": 13,
        "local_pdfs": 13
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Blonde On Blonde.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Blonde On Blonde",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Blonde On Blonde.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 52,
              "errors": 31,
              "error_rate": 59.6
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 13
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 13
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 14
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Blonde On Blonde",
          "pdf_count": 13,
          "total_songs": 13
        },
        "7_local_pdfs": {
          "count": 13
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 59.61538461538461,
      "local_folder": "Bob Dylan\\Bob Dylan - Blonde On Blonde"
    },
    {
      "book_id": "v2-633f0e8d43b59568-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 20,
        "output_files": 20,
        "local_pdfs": 21
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel Greatest Hits Vols 1 And 2.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Billy Joel Greatest Hits Vols 1 And 2",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel Greatest Hits Vols 1 And 2.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 84,
              "errors": 51,
              "error_rate": 60.7
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 20
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 20
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 20
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Billy Joel Greatest Hits Vols 1 And 2",
          "pdf_count": 21,
          "total_songs": 20
        },
        "7_local_pdfs": {
          "count": 21
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 60.71428571428571,
      "local_folder": "Billy Joel\\Billy Joel - Billy Joel Greatest Hits Vols 1 And 2"
    },
    {
      "book_id": "v2-6549b5267cb85b7b-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 46,
        "output_files": 46,
        "local_pdfs": 46
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Anthology.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Anthology",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Anthology.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 193,
              "errors": 78,
              "error_rate": 40.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 46
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 46
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 46
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Anthology",
          "pdf_count": 46,
          "total_songs": 46
        },
        "7_local_pdfs": {
          "count": 46
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 40.41450777202073,
      "local_folder": "Bob Dylan\\Bob Dylan - Anthology"
    },
    {
      "book_id": "v2-66aff583ad276070-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 7,
        "output_files": 7,
        "local_pdfs": 7
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Basement Tapes _PVG_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Basement Tapes _PVG_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Basement Tapes _PVG_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 84,
              "errors": 57,
              "error_rate": 67.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 7
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 7
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 11
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Basement Tapes _PVG_",
          "pdf_count": 7,
          "total_songs": 7
        },
        "7_local_pdfs": {
          "count": 7
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 67.85714285714286,
      "local_folder": "Bob Dylan\\Bob Dylan - Basement Tapes _PVG_"
    },
    {
      "book_id": "v2-672db4e8ffb6a0d8-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 12,
        "output_files": 12,
        "local_pdfs": 12
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Fantasies And Delusions.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Fantasies And Delusions",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Fantasies And Delusions.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 98,
              "errors": 9,
              "error_rate": 9.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 12
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 12
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 17
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Fantasies And Delusions",
          "pdf_count": 12,
          "total_songs": 12
        },
        "7_local_pdfs": {
          "count": 12
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 12
        }
      },
      "page_analysis_error_rate": 9.183673469387756,
      "local_folder": "Billy Joel\\Billy Joel - Fantasies And Delusions"
    },
    {
      "book_id": "v2-6773a6b95e3f78a9-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 12,
        "output_files": 12,
        "local_pdfs": 12
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Live At The Hollywood Bowl.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Live At The Hollywood Bowl",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Live At The Hollywood Bowl.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 36,
              "errors": 23,
              "error_rate": 63.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 12
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 12
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 12
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Live At The Hollywood Bowl",
          "pdf_count": 12,
          "total_songs": 12
        },
        "7_local_pdfs": {
          "count": 12
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 12
        }
      },
      "page_analysis_error_rate": 63.888888888888886,
      "local_folder": "Beatles\\Beatles - Live At The Hollywood Bowl"
    },
    {
      "book_id": "v2-6790e3106cc63c95-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 34,
        "output_files": 34,
        "local_pdfs": 35
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Elton John/Elton John - Greatest Hits 1970-2002.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Elton John",
          "book_name": "Elton John - Greatest Hits 1970-2002",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Elton John/Elton John - Greatest Hits 1970-2002.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 164,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 34
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 34
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 0
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Elton John\\Elton John - Elton John - Greatest Hits 1970-2002",
          "pdf_count": 35,
          "total_songs": 34
        },
        "7_local_pdfs": {
          "count": 35
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 35
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Elton John\\Elton John - Elton John - Greatest Hits 1970-2002"
    },
    {
      "book_id": "v2-6790e3106cc63c95-3",
      "completeness": {
        "exists_count": 9,
        "total_expected": 13,
        "percentage": 69.2
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 34,
        "output_files": 34,
        "local_pdfs": 0
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Elton John/Elton John - Greatest Hits 1970-2002.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Elton John",
          "book_name": "Elton John - Greatest Hits 1970-2002",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Elton John/Elton John - Greatest Hits 1970-2002.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 164,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 34
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 34
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 34
        },
        "6_local_manifest": {
          "exists": false
        },
        "7_local_pdfs": {
          "count": 0
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "N/A"
    },
    {
      "book_id": "v2-6a9717a628808333-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 6,
        "output_files": 6,
        "local_pdfs": 6
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - White Album 1 _Guitar Recorded Version_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "White Album 1 _Guitar Recorded Version_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - White Album 1 _Guitar Recorded Version_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 83,
              "errors": 58,
              "error_rate": 69.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 6
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 6
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 7
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - White Album 1 _Guitar Recorded Version_",
          "pdf_count": 6,
          "total_songs": 6
        },
        "7_local_pdfs": {
          "count": 6
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 6
        }
      },
      "page_analysis_error_rate": 69.87951807228916,
      "local_folder": "Beatles\\Beatles - White Album 1 _Guitar Recorded Version_"
    },
    {
      "book_id": "v2-6dd8547507da3f35-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 17,
        "output_files": 17,
        "local_pdfs": 17
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bread/Bread - Best Of Bread.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bread",
          "book_name": "Best Of Bread",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bread/Bread - Best Of Bread.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 60,
              "errors": 38,
              "error_rate": 63.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 17
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 17
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 17
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bread\\Bread - Best Of Bread",
          "pdf_count": 17,
          "total_songs": 17
        },
        "7_local_pdfs": {
          "count": 17
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 63.33333333333333,
      "local_folder": "Bread\\Bread - Best Of Bread"
    },
    {
      "book_id": "v2-757297be7540fd16-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 22,
        "output_files": 22,
        "local_pdfs": 22
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bonnie Raitt/Bonnie Raitt - Road Tested _PVG Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bonnie Raitt",
          "book_name": "Road Tested _PVG Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bonnie Raitt/Bonnie Raitt - Road Tested _PVG Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 151,
              "errors": 73,
              "error_rate": 48.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 22
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 22
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 26
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bonnie Raitt\\Bonnie Raitt - Road Tested _PVG Book_",
          "pdf_count": 22,
          "total_songs": 22
        },
        "7_local_pdfs": {
          "count": 22
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 48.34437086092716,
      "local_folder": "Bonnie Raitt\\Bonnie Raitt - Road Tested _PVG Book_"
    },
    {
      "book_id": "v2-7775b4415e2875b9-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 10,
        "output_files": 10,
        "local_pdfs": 10
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Highway 61 Revisited.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Highway 61 Revisited",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Highway 61 Revisited.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 36,
              "errors": 21,
              "error_rate": 58.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 10
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 10
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 10
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Highway 61 Revisited",
          "pdf_count": 10,
          "total_songs": 10
        },
        "7_local_pdfs": {
          "count": 10
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 58.333333333333336,
      "local_folder": "Bob Dylan\\Bob Dylan - Highway 61 Revisited"
    },
    {
      "book_id": "v2-77d86a4855e2879e-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 12,
        "output_files": 12,
        "local_pdfs": 12
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/America/America - Greatest Hits _Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "America",
          "book_name": "Greatest Hits _Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/America/America - Greatest Hits _Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 62,
              "errors": 33,
              "error_rate": 53.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 12
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 12
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 12
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "America\\America - Greatest Hits _Book_",
          "pdf_count": 12,
          "total_songs": 12
        },
        "7_local_pdfs": {
          "count": 12
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 12
        }
      },
      "page_analysis_error_rate": 53.2258064516129,
      "local_folder": "America\\America - Greatest Hits _Book_"
    },
    {
      "book_id": "v2-7a06403f9019923a-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 49,
        "output_files": 49,
        "local_pdfs": 49
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Complete Vol 2.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Complete Vol 2",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Complete Vol 2.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 293,
              "errors": 14,
              "error_rate": 4.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 49
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 49
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 49
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Complete Vol 2",
          "pdf_count": 49,
          "total_songs": 49
        },
        "7_local_pdfs": {
          "count": 49
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 49
        }
      },
      "page_analysis_error_rate": 4.778156996587031,
      "local_folder": "Billy Joel\\Billy Joel - Complete Vol 2"
    },
    {
      "book_id": "v2-7f971a078a2bcaab-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 9,
        "output_files": 9,
        "local_pdfs": 4
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Anthology 3 page_80_-_111.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Anthology 3 page_80_-_111",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Anthology 3 page_80_-_111.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 33,
              "errors": 24,
              "error_rate": 72.7
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 9
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 9
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 10
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Anthology 3 page_80_-_111",
          "pdf_count": 4,
          "total_songs": 9
        },
        "7_local_pdfs": {
          "count": 4
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 4
        }
      },
      "page_analysis_error_rate": 72.72727272727273,
      "local_folder": "Beatles\\Beatles - Anthology 3 page_80_-_111"
    },
    {
      "book_id": "v2-818f017b6ced8b83-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 12,
        "output_files": 12,
        "local_pdfs": 13
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Ben Folds/Ben Folds Five - Whatever And Ever Amen _Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Ben Folds",
          "book_name": "Whatever And Ever Amen _Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Ben Folds/Ben Folds Five - Whatever And Ever Amen _Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 141,
              "errors": 91,
              "error_rate": 64.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 12
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 12
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 12
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Ben Folds\\Ben Folds - Whatever And Ever Amen _Book_",
          "pdf_count": 13,
          "total_songs": 12
        },
        "7_local_pdfs": {
          "count": 13
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 13
        }
      },
      "page_analysis_error_rate": 64.53900709219859,
      "local_folder": "Ben Folds\\Ben Folds - Whatever And Ever Amen _Book_"
    },
    {
      "book_id": "v2-84fd7f5577e64b71-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 6,
        "output_files": 6,
        "local_pdfs": 6
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Ben Folds/Ben Folds - Rockin The Suburbs _Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Ben Folds",
          "book_name": "Rockin The Suburbs _Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Ben Folds/Ben Folds - Rockin The Suburbs _Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 86,
              "errors": 51,
              "error_rate": 59.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 6
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 6
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 8
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Ben Folds\\Ben Folds - Rockin The Suburbs _Book_",
          "pdf_count": 6,
          "total_songs": 6
        },
        "7_local_pdfs": {
          "count": 6
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 6
        }
      },
      "page_analysis_error_rate": 59.30232558139535,
      "local_folder": "Ben Folds\\Ben Folds - Rockin The Suburbs _Book_"
    },
    {
      "book_id": "v2-8529f671e68d4eee-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 26,
        "output_files": 26,
        "local_pdfs": 26
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Anthology 2 page_01_-_40.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Anthology 2 page_01_-_40",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Anthology 2 page_01_-_40.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 40,
              "errors": 25,
              "error_rate": 62.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 26
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 26
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 26
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Anthology 2 page_01_-_40",
          "pdf_count": 26,
          "total_songs": 26
        },
        "7_local_pdfs": {
          "count": 26
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 26
        }
      },
      "page_analysis_error_rate": 62.5,
      "local_folder": "Beatles\\Beatles - Anthology 2 page_01_-_40"
    },
    {
      "book_id": "v2-891cfa3eccc19933",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 9,
        "output_files": 9,
        "local_pdfs": 9
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - 52nd Street.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Billy Joel - 52nd Street",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - 52nd Street.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 59,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 9
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 9
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 9
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - 52nd Street",
          "pdf_count": 9,
          "total_songs": 9
        },
        "7_local_pdfs": {
          "count": 9
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Billy Joel\\Billy Joel - 52nd Street"
    },
    {
      "book_id": "v2-891cfa3eccc19933-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 9,
        "output_files": 9,
        "local_pdfs": 9
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - 52nd Street.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Billy Joel - 52nd Street",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - 52nd Street.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 59,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 9
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 9
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 0
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Billy Joel - 52nd Street",
          "pdf_count": 9,
          "total_songs": 9
        },
        "7_local_pdfs": {
          "count": 9
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 9
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Billy Joel\\Billy Joel - Billy Joel - 52nd Street"
    },
    {
      "book_id": "v2-891cfa3eccc19933-3",
      "completeness": {
        "exists_count": 9,
        "total_expected": 13,
        "percentage": 69.2
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 9,
        "output_files": 9,
        "local_pdfs": 0
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - 52nd Street.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Billy Joel - 52nd Street",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - 52nd Street.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 59,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 9
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 9
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 9
        },
        "6_local_manifest": {
          "exists": false
        },
        "7_local_pdfs": {
          "count": 0
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "N/A"
    },
    {
      "book_id": "v2-8f1f0f7cb41370f6-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 178,
        "output_files": 178,
        "local_pdfs": 178
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Complete Scores _2_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Complete Scores _2_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Complete Scores _2_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 1120,
              "errors": 181,
              "error_rate": 16.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 178
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 178
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 178
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Complete Scores _2_",
          "pdf_count": 178,
          "total_songs": 178
        },
        "7_local_pdfs": {
          "count": 178
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 178
        }
      },
      "page_analysis_error_rate": 16.16071428571429,
      "local_folder": "Beatles\\Beatles - Complete Scores _2_"
    },
    {
      "book_id": "v2-8fb3713b5f204458-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 50,
        "output_files": 50,
        "local_pdfs": 50
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Anthology 2.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Anthology 2",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Anthology 2.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 202,
              "errors": 76,
              "error_rate": 37.6
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 50
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 50
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 50
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Anthology 2",
          "pdf_count": 50,
          "total_songs": 50
        },
        "7_local_pdfs": {
          "count": 50
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 37.62376237623762,
      "local_folder": "Bob Dylan\\Bob Dylan - Anthology 2"
    },
    {
      "book_id": "v2-91689598a6ca3eea-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 10,
        "output_files": 10,
        "local_pdfs": 9
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Creedence Clearwater Revival/Creedence Clearwater Revival - 8 Pcs Book.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Creedence Clearwater Revival",
          "book_name": "8 Pcs Book",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Creedence Clearwater Revival/Creedence Clearwater Revival - 8 Pcs Book.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 20,
              "errors": 13,
              "error_rate": 65.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 10
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 10
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 9
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Creedence Clearwater Revival\\Creedence Clearwater Revival - 8 Pcs Book",
          "pdf_count": 9,
          "total_songs": 10
        },
        "7_local_pdfs": {
          "count": 9
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 65.0,
      "local_folder": "Creedence Clearwater Revival\\Creedence Clearwater Revival - 8 Pcs Book"
    },
    {
      "book_id": "v2-954d269a2a8e9388-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 174,
        "output_files": 174,
        "local_pdfs": 192
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Fake Songbook _Guitar_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Fake Songbook _Guitar_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Fake Songbook _Guitar_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 732,
              "errors": 50,
              "error_rate": 6.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 174
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 174
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 236
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Fake Songbook _Guitar_",
          "pdf_count": 192,
          "total_songs": 428
        },
        "7_local_pdfs": {
          "count": 192
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 192
        }
      },
      "page_analysis_error_rate": 6.830601092896176,
      "local_folder": "Beatles\\Beatles - Fake Songbook _Guitar_"
    },
    {
      "book_id": "v2-95fe4beb77ebc01e-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 22,
        "output_files": 22,
        "local_pdfs": 22
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bon Jovi/Bon Jovi - Best Of Bon Jovi.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bon Jovi",
          "book_name": "Best Of Bon Jovi",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bon Jovi/Bon Jovi - Best Of Bon Jovi.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 240,
              "errors": 98,
              "error_rate": 40.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 22
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 22
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 22
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bon Jovi\\Bon Jovi - Best Of Bon Jovi",
          "pdf_count": 22,
          "total_songs": 22
        },
        "7_local_pdfs": {
          "count": 22
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 40.833333333333336,
      "local_folder": "Bon Jovi\\Bon Jovi - Best Of Bon Jovi"
    },
    {
      "book_id": "v2-96dcb5640de4e270-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 27,
        "output_files": 27,
        "local_pdfs": 27
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Anthology 1 _113 pages_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Anthology 1 _113 pages_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Anthology 1 _113 pages_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 113,
              "errors": 45,
              "error_rate": 39.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 27
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 27
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 27
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Anthology 1 _113 pages_",
          "pdf_count": 27,
          "total_songs": 27
        },
        "7_local_pdfs": {
          "count": 27
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 27
        }
      },
      "page_analysis_error_rate": 39.823008849557525,
      "local_folder": "Beatles\\Beatles - Anthology 1 _113 pages_"
    },
    {
      "book_id": "v2-9a5487d438dc0e6a-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 27,
        "output_files": 27,
        "local_pdfs": 27
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Greatest Hits Vol I And II.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Greatest Hits Vol I And II",
          "songs_extracted": 27,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Greatest Hits Vol I And II.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 131,
              "errors": 28,
              "error_rate": 21.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 27
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 27
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 27
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Greatest Hits Vol I And II",
          "pdf_count": 27,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 27
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 27
        }
      },
      "page_analysis_error_rate": 21.374045801526716,
      "local_folder": "Billy Joel\\Billy Joel - Greatest Hits Vol I And II"
    },
    {
      "book_id": "v2-9e00e5132ca822db-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 10,
        "output_files": 10,
        "local_pdfs": 10
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Glass Houses.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Glass Houses",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Glass Houses.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 66,
              "errors": 11,
              "error_rate": 16.7
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 10
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 10
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 10
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Glass Houses",
          "pdf_count": 10,
          "total_songs": 10
        },
        "7_local_pdfs": {
          "count": 10
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 10
        }
      },
      "page_analysis_error_rate": 16.666666666666664,
      "local_folder": "Billy Joel\\Billy Joel - Glass Houses"
    },
    {
      "book_id": "v2-a0911025aeedcf07-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 11,
        "output_files": 11,
        "local_pdfs": 11
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Asia/Asia - Alpha _PVG Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Asia",
          "book_name": "Alpha _PVG Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Asia/Asia - Alpha _PVG Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 60,
              "errors": 32,
              "error_rate": 53.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 11
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 11
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 11
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Asia\\Asia - Alpha _PVG Book_",
          "pdf_count": 11,
          "total_songs": 11
        },
        "7_local_pdfs": {
          "count": 11
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 11
        }
      },
      "page_analysis_error_rate": 53.333333333333336,
      "local_folder": "Asia\\Asia - Alpha _PVG Book_"
    },
    {
      "book_id": "v2-a4399dcb8758a9b3-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 17,
        "output_files": 17,
        "local_pdfs": 17
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Colbie Caillat/Colbie Caillat - Breakthrough _PVG Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Colbie Caillat",
          "book_name": "Breakthrough _PVG Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Colbie Caillat/Colbie Caillat - Breakthrough _PVG Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 75,
              "errors": 45,
              "error_rate": 60.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 17
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 17
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 17
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Colbie Caillat\\Colbie Caillat - Breakthrough _PVG Book_",
          "pdf_count": 17,
          "total_songs": 17
        },
        "7_local_pdfs": {
          "count": 17
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 60.0,
      "local_folder": "Colbie Caillat\\Colbie Caillat - Breakthrough _PVG Book_"
    },
    {
      "book_id": "v2-a5716c19eea03c55-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 13,
        "output_files": 13,
        "local_pdfs": 13
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Black Eyed Peas/Black Eyed Peas - Elephunk _PVG Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Black Eyed Peas",
          "book_name": "Elephunk _PVG Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Black Eyed Peas/Black Eyed Peas - Elephunk _PVG Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 136,
              "errors": 87,
              "error_rate": 64.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 13
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 13
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 13
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Black Eyed Peas\\Black Eyed Peas - Elephunk _PVG Book_",
          "pdf_count": 13,
          "total_songs": 13
        },
        "7_local_pdfs": {
          "count": 13
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 63.970588235294116,
      "local_folder": "Black Eyed Peas\\Black Eyed Peas - Elephunk _PVG Book_"
    },
    {
      "book_id": "v2-a9198ca7b123a968-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 10,
        "output_files": 10,
        "local_pdfs": 10
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Ocean/Billy Ocean - The Best Of.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Ocean",
          "book_name": "The Best Of",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Ocean/Billy Ocean - The Best Of.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 60,
              "errors": 24,
              "error_rate": 40.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 10
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 10
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 10
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Ocean\\Billy Ocean - The Best Of",
          "pdf_count": 10,
          "total_songs": 10
        },
        "7_local_pdfs": {
          "count": 10
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 40.0,
      "local_folder": "Billy Ocean\\Billy Ocean - The Best Of"
    },
    {
      "book_id": "v2-a9e7de857865e3ef-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 6,
        "output_files": 6,
        "local_pdfs": 6
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Ben Folds/Ben Folds - Songs For Silverman.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Ben Folds",
          "book_name": "Songs For Silverman",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Ben Folds/Ben Folds - Songs For Silverman.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 94,
              "errors": 59,
              "error_rate": 62.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 6
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 6
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 7
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Ben Folds\\Ben Folds - Songs For Silverman",
          "pdf_count": 6,
          "total_songs": 6
        },
        "7_local_pdfs": {
          "count": 6
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 6
        }
      },
      "page_analysis_error_rate": 62.76595744680851,
      "local_folder": "Ben Folds\\Ben Folds - Songs For Silverman"
    },
    {
      "book_id": "v2-af3cb91e43ccb9e6-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 14,
        "output_files": 14,
        "local_pdfs": 14
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Revolver.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Revolver",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Revolver.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 96,
              "errors": 58,
              "error_rate": 60.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 14
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 14
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 15
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Revolver",
          "pdf_count": 14,
          "total_songs": 14
        },
        "7_local_pdfs": {
          "count": 14
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 14
        }
      },
      "page_analysis_error_rate": 60.416666666666664,
      "local_folder": "Beatles\\Beatles - Revolver"
    },
    {
      "book_id": "v2-afb1ddb62a763743-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 35,
        "output_files": 35,
        "local_pdfs": 35
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carole King/Carole King - Classics _3_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carole King",
          "book_name": "Classics _3_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carole King/Carole King - Classics _3_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 128,
              "errors": 69,
              "error_rate": 53.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 35
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 35
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 35
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carole King\\Carole King - Classics _3_",
          "pdf_count": 35,
          "total_songs": 35
        },
        "7_local_pdfs": {
          "count": 35
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 53.90625,
      "local_folder": "Carole King\\Carole King - Classics _3_"
    },
    {
      "book_id": "v2-b1c5d9e0b2c00cfa-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 29,
        "output_files": 29,
        "local_pdfs": 29
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Allman Brothers/Allman Brothers - Best Of _PVG_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Allman Brothers",
          "book_name": "Best Of _PVG_",
          "songs_extracted": 29,
          "source_pdf_uri": "s3://jsmith-input/Allman Brothers/Allman Brothers - Best Of _PVG_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 170,
              "errors": 19,
              "error_rate": 11.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 29
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 29
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 29
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Allman Brothers\\Allman Brothers - Best Of _PVG_",
          "pdf_count": 29,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 29
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 29
        }
      },
      "page_analysis_error_rate": 11.176470588235295,
      "local_folder": "Allman Brothers\\Allman Brothers - Best Of _PVG_"
    },
    {
      "book_id": "v2-b35285e7019e260e-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 26,
        "output_files": 26,
        "local_pdfs": 26
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Singles Collection _PVG_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Singles Collection _PVG_",
          "songs_extracted": 26,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Singles Collection _PVG_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 97,
              "errors": 13,
              "error_rate": 13.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 26
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 26
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 26
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Singles Collection _PVG_",
          "pdf_count": 26,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 26
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 26
        }
      },
      "page_analysis_error_rate": 13.402061855670103,
      "local_folder": "Beatles\\Beatles - Singles Collection _PVG_"
    },
    {
      "book_id": "v2-b4675a1cadde74b1-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 56,
        "output_files": 56,
        "local_pdfs": 56
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Beatlemania 1963-1966.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Beatlemania 1963-1966",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Beatlemania 1963-1966.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 128,
              "errors": 54,
              "error_rate": 42.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 56
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 56
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 56
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Beatlemania 1963-1966",
          "pdf_count": 56,
          "total_songs": 56
        },
        "7_local_pdfs": {
          "count": 56
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 56
        }
      },
      "page_analysis_error_rate": 42.1875,
      "local_folder": "Beatles\\Beatles - Beatlemania 1963-1966"
    },
    {
      "book_id": "v2-b6d0b290c4b93896-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 5,
        "output_files": 5,
        "local_pdfs": 5
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Ben Folds/Ben Folds - Songs For The Silverman.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Ben Folds",
          "book_name": "Songs For The Silverman",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Ben Folds/Ben Folds - Songs For The Silverman.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 94,
              "errors": 62,
              "error_rate": 66.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 5
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 5
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 6
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Ben Folds\\Ben Folds - Songs For The Silverman",
          "pdf_count": 5,
          "total_songs": 5
        },
        "7_local_pdfs": {
          "count": 5
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 5
        }
      },
      "page_analysis_error_rate": 65.95744680851064,
      "local_folder": "Ben Folds\\Ben Folds - Songs For The Silverman"
    },
    {
      "book_id": "v2-c2a89cc21678f463",
      "completeness": {
        "exists_count": 8,
        "total_expected": 13,
        "percentage": 61.5
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 6,
        "output_files": 6,
        "local_pdfs": 0
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Queen/Queen - Greatest Hits.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "processing",
          "artist": "Queen",
          "book_name": "Greatest Hits",
          "songs_extracted": null,
          "source_pdf_uri": "s3://jsmith-input/Queen/Queen - Greatest Hits.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 34,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 6
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 6
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": false
        },
        "5_s3_output_pdfs": {
          "count": 6
        },
        "6_local_manifest": {
          "exists": false
        },
        "7_local_pdfs": {
          "count": 0
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "N/A"
    },
    {
      "book_id": "v2-c2a89cc21678f463-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 6,
        "output_files": 6,
        "local_pdfs": 7
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Queen/Queen - Greatest Hits.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Queen",
          "book_name": "Queen - Greatest Hits",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Queen/Queen - Greatest Hits.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 34,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 6
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 6
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 0
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Queen\\Queen - Queen - Greatest Hits",
          "pdf_count": 7,
          "total_songs": 6
        },
        "7_local_pdfs": {
          "count": 7
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 7
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Queen\\Queen - Queen - Greatest Hits"
    },
    {
      "book_id": "v2-c2a89cc21678f463-3",
      "completeness": {
        "exists_count": 9,
        "total_expected": 13,
        "percentage": 69.2
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 1,
        "output_files": 1,
        "local_pdfs": 0
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Queen/Queen - Greatest Hits.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Queen",
          "book_name": "Queen - Greatest Hits",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Queen/Queen - Greatest Hits.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 34,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 1
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 1
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 6
        },
        "6_local_manifest": {
          "exists": false
        },
        "7_local_pdfs": {
          "count": 0
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "N/A"
    },
    {
      "book_id": "v2-c2a89cc21678f463-4",
      "completeness": {
        "exists_count": 9,
        "total_expected": 13,
        "percentage": 69.2
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 6,
        "output_files": 6,
        "local_pdfs": 0
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Queen/Queen - Greatest Hits.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Queen",
          "book_name": "Queen - Greatest Hits",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Queen/Queen - Greatest Hits.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 34,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 6
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 6
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 6
        },
        "6_local_manifest": {
          "exists": false
        },
        "7_local_pdfs": {
          "count": 0
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "N/A"
    },
    {
      "book_id": "v2-c2a89cc21678f463-5",
      "completeness": {
        "exists_count": 9,
        "total_expected": 13,
        "percentage": 69.2
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 6,
        "output_files": 6,
        "local_pdfs": 0
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Queen/Queen - Greatest Hits.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Queen",
          "book_name": "Queen - Greatest Hits",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Queen/Queen - Greatest Hits.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 34,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 6
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 6
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 6
        },
        "6_local_manifest": {
          "exists": false
        },
        "7_local_pdfs": {
          "count": 0
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "N/A"
    },
    {
      "book_id": "v2-c5007b2b55e9cd92-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 4,
        "output_files": 4,
        "local_pdfs": 4
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Anthology 2 page_41_-72.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Anthology 2 page_41_-72",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Anthology 2 page_41_-72.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 32,
              "errors": 15,
              "error_rate": 46.9
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 4
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 4
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 5
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Anthology 2 page_41_-72",
          "pdf_count": 4,
          "total_songs": 4
        },
        "7_local_pdfs": {
          "count": 4
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 4
        }
      },
      "page_analysis_error_rate": 46.875,
      "local_folder": "Beatles\\Beatles - Anthology 2 page_41_-72"
    },
    {
      "book_id": "v2-c59bad373f7d2f2b-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 9,
        "output_files": 9,
        "local_pdfs": 9
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Allman Brothers/Allman Brothers - Band Best _Score_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Allman Brothers",
          "book_name": "Band Best _Score_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Allman Brothers/Allman Brothers - Band Best _Score_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 114,
              "errors": 54,
              "error_rate": 47.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 9
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 9
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 10
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Allman Brothers\\Allman Brothers - Band Best _Score_",
          "pdf_count": 9,
          "total_songs": 9
        },
        "7_local_pdfs": {
          "count": 9
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 9
        }
      },
      "page_analysis_error_rate": 47.368421052631575,
      "local_folder": "Allman Brothers\\Allman Brothers - Band Best _Score_"
    },
    {
      "book_id": "v2-ce9d957468e199fe-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 13,
        "output_files": 13,
        "local_pdfs": 13
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Barry Manilow/Barry Manilow - Barry Manilow _PVG Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Barry Manilow",
          "book_name": "Barry Manilow _PVG Book_",
          "songs_extracted": 13,
          "source_pdf_uri": "s3://jsmith-input/Barry Manilow/Barry Manilow - Barry Manilow _PVG Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 79,
              "errors": 2,
              "error_rate": 2.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 13
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 13
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 13
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Barry Manilow\\Barry Manilow - Barry Manilow _PVG Book_",
          "pdf_count": 13,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 13
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 13
        }
      },
      "page_analysis_error_rate": 2.5316455696202533,
      "local_folder": "Barry Manilow\\Barry Manilow - Barry Manilow _PVG Book_"
    },
    {
      "book_id": "v2-cfffd4fe38c715a7-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 7,
        "output_files": 7,
        "local_pdfs": 7
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Abbey Road Guitar Recorded Version.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Abbey Road Guitar Recorded Version",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Abbey Road Guitar Recorded Version.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 108,
              "errors": 51,
              "error_rate": 47.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 7
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 7
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 13
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Abbey Road Guitar Recorded Version",
          "pdf_count": 7,
          "total_songs": 7
        },
        "7_local_pdfs": {
          "count": 7
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 7
        }
      },
      "page_analysis_error_rate": 47.22222222222222,
      "local_folder": "Beatles\\Beatles - Abbey Road Guitar Recorded Version"
    },
    {
      "book_id": "v2-d35477b4781fcc7f-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 15,
        "output_files": 15,
        "local_pdfs": 15
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Keyboard Book.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Keyboard Book",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Keyboard Book.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 151,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 15
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 15
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 15
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Keyboard Book",
          "pdf_count": 15,
          "total_songs": 15
        },
        "7_local_pdfs": {
          "count": 15
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 15
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Billy Joel\\Billy Joel - Keyboard Book"
    },
    {
      "book_id": "v2-d4e31687ff9a300e-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 5,
        "output_files": 5,
        "local_pdfs": 5
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Cheap Trick/Cheap Trick - Greatest Hits _Score_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Cheap Trick",
          "book_name": "Greatest Hits _Score_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Cheap Trick/Cheap Trick - Greatest Hits _Score_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 110,
              "errors": 81,
              "error_rate": 73.6
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 5
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 5
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 5
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Cheap Trick\\Cheap Trick - Greatest Hits _Score_",
          "pdf_count": 5,
          "total_songs": 5
        },
        "7_local_pdfs": {
          "count": 5
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 73.63636363636363,
      "local_folder": "Cheap Trick\\Cheap Trick - Greatest Hits _Score_"
    },
    {
      "book_id": "v2-d5a9286f0899e26e-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 11,
        "output_files": 11,
        "local_pdfs": 11
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Seger/Bob Seger - The New Best Of Bob Seger.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Seger",
          "book_name": "The New Best Of Bob Seger",
          "songs_extracted": 11,
          "source_pdf_uri": "s3://jsmith-input/Bob Seger/Bob Seger - The New Best Of Bob Seger.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 33,
              "errors": 9,
              "error_rate": 27.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 11
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 11
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 11
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Seger\\Bob Seger - The New Best Of Bob Seger",
          "pdf_count": 11,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 11
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 11
        }
      },
      "page_analysis_error_rate": 27.27272727272727,
      "local_folder": "Bob Seger\\Bob Seger - The New Best Of Bob Seger"
    },
    {
      "book_id": "v2-d62ee23e1078c348-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 6,
        "output_files": 6,
        "local_pdfs": 2
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Anthology 3 _page 37 - 79.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Anthology 3 _page 37 - 79",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Anthology 3 _page 37 - 79.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 43,
              "errors": 33,
              "error_rate": 76.7
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 6
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 6
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 8
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Anthology 3 _page 37 - 79",
          "pdf_count": 2,
          "total_songs": 6
        },
        "7_local_pdfs": {
          "count": 2
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 2
        }
      },
      "page_analysis_error_rate": 76.74418604651163,
      "local_folder": "Beatles\\Beatles - Anthology 3 _page 37 - 79"
    },
    {
      "book_id": "v2-d88d078df9761c30-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 16,
        "output_files": 16,
        "local_pdfs": 16
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Allman Brothers/Allman Brothers - Allman Brothers Band _PVG_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Allman Brothers",
          "book_name": "Allman Brothers Band _PVG_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Allman Brothers/Allman Brothers - Allman Brothers Band _PVG_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 96,
              "errors": 33,
              "error_rate": 34.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 16
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 16
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 16
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Allman Brothers\\Allman Brothers - Allman Brothers Band _PVG_",
          "pdf_count": 16,
          "total_songs": 16
        },
        "7_local_pdfs": {
          "count": 16
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 16
        }
      },
      "page_analysis_error_rate": 34.375,
      "local_folder": "Allman Brothers\\Allman Brothers - Allman Brothers Band _PVG_"
    },
    {
      "book_id": "v2-dc0f8d02fb8d3624-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 12,
        "output_files": 12,
        "local_pdfs": 12
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - For Advanced Piano.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "For Advanced Piano",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - For Advanced Piano.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 82,
              "errors": 10,
              "error_rate": 12.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 12
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 12
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 13
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - For Advanced Piano",
          "pdf_count": 12,
          "total_songs": 12
        },
        "7_local_pdfs": {
          "count": 12
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 12
        }
      },
      "page_analysis_error_rate": 12.195121951219512,
      "local_folder": "Billy Joel\\Billy Joel - For Advanced Piano"
    },
    {
      "book_id": "v2-dc4c90d5e3d7da00",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 17,
        "output_files": 17,
        "local_pdfs": 20
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Abbey Road.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Beatles - Abbey Road",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Abbey Road.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 59,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 17
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 17
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 17
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Abbey Road",
          "pdf_count": 20,
          "total_songs": 17
        },
        "7_local_pdfs": {
          "count": 20
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Beatles\\Beatles - Abbey Road"
    },
    {
      "book_id": "v2-dc4c90d5e3d7da00-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 17,
        "output_files": 17,
        "local_pdfs": 18
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Abbey Road.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Beatles - Abbey Road",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Abbey Road.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 59,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 17
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 17
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 0
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Beatles - Abbey Road",
          "pdf_count": 18,
          "total_songs": 17
        },
        "7_local_pdfs": {
          "count": 18
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 18
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Beatles\\Beatles - Beatles - Abbey Road"
    },
    {
      "book_id": "v2-dc4c90d5e3d7da00-3",
      "completeness": {
        "exists_count": 9,
        "total_expected": 13,
        "percentage": 69.2
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 17,
        "output_files": 17,
        "local_pdfs": 0
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Abbey Road.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Beatles - Abbey Road",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Abbey Road.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 59,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 17
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 17
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 17
        },
        "6_local_manifest": {
          "exists": false
        },
        "7_local_pdfs": {
          "count": 0
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "N/A"
    },
    {
      "book_id": "v2-dde323032f955172-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 21,
        "output_files": 21,
        "local_pdfs": 21
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Greatest Hits.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Greatest Hits",
          "songs_extracted": 21,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Greatest Hits.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 138,
              "errors": 23,
              "error_rate": 16.7
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 21
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 21
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 21
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Greatest Hits",
          "pdf_count": 21,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 21
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 21
        }
      },
      "page_analysis_error_rate": 16.666666666666664,
      "local_folder": "Billy Joel\\Billy Joel - Greatest Hits"
    },
    {
      "book_id": "v2-e1714150fcf3f966-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 70,
        "output_files": 70,
        "local_pdfs": 70
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - My Lives.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "My Lives",
          "songs_extracted": 70,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - My Lives.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 430,
              "errors": 32,
              "error_rate": 7.4
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 70
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 70
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 70
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - My Lives",
          "pdf_count": 70,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 70
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 70
        }
      },
      "page_analysis_error_rate": 7.441860465116279,
      "local_folder": "Billy Joel\\Billy Joel - My Lives"
    },
    {
      "book_id": "v2-e22444fd4d72d1a7-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 12,
        "output_files": 12,
        "local_pdfs": 12
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - The Harp Styles Of Bob Dylan _Harmonica_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "The Harp Styles Of Bob Dylan _Harmonica_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - The Harp Styles Of Bob Dylan _Harmonica_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 73,
              "errors": 48,
              "error_rate": 65.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 12
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 12
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 12
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - The Harp Styles Of Bob Dylan _Harmonica_",
          "pdf_count": 12,
          "total_songs": 12
        },
        "7_local_pdfs": {
          "count": 12
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 65.75342465753424,
      "local_folder": "Bob Dylan\\Bob Dylan - The Harp Styles Of Bob Dylan _Harmonica_"
    },
    {
      "book_id": "v2-e32e7feb95c5dd5b-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 15,
        "output_files": 15,
        "local_pdfs": 15
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Aerosmith/Aerosmith - Greatest Hits _Songbook_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Aerosmith",
          "book_name": "Greatest Hits _Songbook_",
          "songs_extracted": 15,
          "source_pdf_uri": "s3://jsmith-input/Aerosmith/Aerosmith - Greatest Hits _Songbook_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 80,
              "errors": 1,
              "error_rate": 1.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 15
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 15
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 15
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Aerosmith\\Aerosmith - Greatest Hits _Songbook_",
          "pdf_count": 15,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 15
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 15
        }
      },
      "page_analysis_error_rate": 1.25,
      "local_folder": "Aerosmith\\Aerosmith - Greatest Hits _Songbook_"
    },
    {
      "book_id": "v2-e3d88bf7f64722be-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 11,
        "output_files": 11,
        "local_pdfs": 11
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Billy Joel/Billy Joel - Songs In The Attic.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Billy Joel",
          "book_name": "Songs In The Attic",
          "songs_extracted": 11,
          "source_pdf_uri": "s3://jsmith-input/Billy Joel/Billy Joel - Songs In The Attic.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 52,
              "errors": 15,
              "error_rate": 28.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 11
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 11
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 11
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Billy Joel\\Billy Joel - Songs In The Attic",
          "pdf_count": 11,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 11
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 11
        }
      },
      "page_analysis_error_rate": 28.846153846153843,
      "local_folder": "Billy Joel\\Billy Joel - Songs In The Attic"
    },
    {
      "book_id": "v2-e63dd599caa89c37-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 7,
        "output_files": 7,
        "local_pdfs": 7
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bonnie Tyler/Bonnie Tyler - Hot Songs.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bonnie Tyler",
          "book_name": "Hot Songs",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bonnie Tyler/Bonnie Tyler - Hot Songs.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 40,
              "errors": 18,
              "error_rate": 45.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 7
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 7
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 7
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bonnie Tyler\\Bonnie Tyler - Hot Songs",
          "pdf_count": 7,
          "total_songs": 7
        },
        "7_local_pdfs": {
          "count": 7
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 45.0,
      "local_folder": "Bonnie Tyler\\Bonnie Tyler - Hot Songs"
    },
    {
      "book_id": "v2-e742d8703640e367-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 2,
        "output_files": 2,
        "local_pdfs": 2
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Finger Picking.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Finger Picking",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Finger Picking.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 48,
              "errors": 33,
              "error_rate": 68.8
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 2
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 2
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 4
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Finger Picking",
          "pdf_count": 2,
          "total_songs": 2
        },
        "7_local_pdfs": {
          "count": 2
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 68.75,
      "local_folder": "Bob Dylan\\Bob Dylan - Finger Picking"
    },
    {
      "book_id": "v2-e7f5c9b4b084d80e-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 21,
        "output_files": 21,
        "local_pdfs": 20
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Collection.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Collection",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Collection.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 196,
              "errors": 102,
              "error_rate": 52.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 21
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 21
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 27
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Collection",
          "pdf_count": 20,
          "total_songs": 21
        },
        "7_local_pdfs": {
          "count": 20
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 52.04081632653062,
      "local_folder": "Bob Dylan\\Bob Dylan - Collection"
    },
    {
      "book_id": "v2-ec007edaef9b222a-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "INCONSISTENT",
        "verified_songs": 8,
        "output_files": 8,
        "local_pdfs": 7
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Saved.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bob Dylan",
          "book_name": "Saved",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bob Dylan/Bob Dylan - Saved.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 54,
              "errors": 37,
              "error_rate": 68.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 8
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 8
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 8
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bob Dylan\\Bob Dylan - Saved",
          "pdf_count": 7,
          "total_songs": 8
        },
        "7_local_pdfs": {
          "count": 7
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 68.51851851851852,
      "local_folder": "Bob Dylan\\Bob Dylan - Saved"
    },
    {
      "book_id": "v2-edb4053730a5cad5-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 19,
        "output_files": 19,
        "local_pdfs": 19
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Carole King/Carole King - The New Best Of Carole King.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Carole King",
          "book_name": "The New Best Of Carole King",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Carole King/Carole King - The New Best Of Carole King.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 66,
              "errors": 36,
              "error_rate": 54.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 19
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 19
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 19
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Carole King\\Carole King - The New Best Of Carole King",
          "pdf_count": 19,
          "total_songs": 19
        },
        "7_local_pdfs": {
          "count": 19
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 54.54545454545454,
      "local_folder": "Carole King\\Carole King - The New Best Of Carole King"
    },
    {
      "book_id": "v2-ee63e83296645419-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 92,
        "output_files": 92,
        "local_pdfs": 92
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - 100 Hits For All Keyboards.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "100 Hits For All Keyboards",
          "songs_extracted": 92,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - 100 Hits For All Keyboards.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 209,
              "errors": 25,
              "error_rate": 12.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 92
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 92
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 92
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - 100 Hits For All Keyboards",
          "pdf_count": 92,
          "total_songs": 0
        },
        "7_local_pdfs": {
          "count": 92
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 92
        }
      },
      "page_analysis_error_rate": 11.961722488038278,
      "local_folder": "Beatles\\Beatles - 100 Hits For All Keyboards"
    },
    {
      "book_id": "v2-ee8ea8398df456e5-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 41,
        "output_files": 41,
        "local_pdfs": 41
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Burt Bacharach/Burt Bacharach - Anthology.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Burt Bacharach",
          "book_name": "Anthology",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Burt Bacharach/Burt Bacharach - Anthology.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 155,
              "errors": 72,
              "error_rate": 46.5
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 41
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 41
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 41
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Burt Bacharach\\Burt Bacharach - Anthology",
          "pdf_count": 41,
          "total_songs": 41
        },
        "7_local_pdfs": {
          "count": 41
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 46.45161290322581,
      "local_folder": "Burt Bacharach\\Burt Bacharach - Anthology"
    },
    {
      "book_id": "v2-eed353908a64f3bb-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 13,
        "output_files": 13,
        "local_pdfs": 13
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/America/America - America _PVG Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "America",
          "book_name": "America _PVG Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/America/America - America _PVG Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 59,
              "errors": 32,
              "error_rate": 54.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 13
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 13
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 13
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "America\\America - America _PVG Book_",
          "pdf_count": 13,
          "total_songs": 13
        },
        "7_local_pdfs": {
          "count": 13
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 13
        }
      },
      "page_analysis_error_rate": 54.23728813559322,
      "local_folder": "America\\America - America _PVG Book_"
    },
    {
      "book_id": "v2-f8b91626f49d2cc6-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 5,
        "output_files": 5,
        "local_pdfs": 5
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Joy Of Beatles.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Joy Of Beatles",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Joy Of Beatles.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 42,
              "errors": 21,
              "error_rate": 50.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 5
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 5
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 9
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Joy Of Beatles",
          "pdf_count": 5,
          "total_songs": 5
        },
        "7_local_pdfs": {
          "count": 5
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 5
        }
      },
      "page_analysis_error_rate": 50.0,
      "local_folder": "Beatles\\Beatles - Joy Of Beatles"
    },
    {
      "book_id": "v2-f8ec20dce8b730ee-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 12,
        "output_files": 12,
        "local_pdfs": 12
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Adele/Adele - 19 _PVG Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Adele",
          "book_name": "19 _PVG Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Adele/Adele - 19 _PVG Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 67,
              "errors": 43,
              "error_rate": 64.2
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 12
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 12
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 12
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Adele\\Adele - 19 _PVG Book_",
          "pdf_count": 12,
          "total_songs": 12
        },
        "7_local_pdfs": {
          "count": 12
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 12
        }
      },
      "page_analysis_error_rate": 64.17910447761194,
      "local_folder": "Adele\\Adele - 19 _PVG Book_"
    },
    {
      "book_id": "v2-f9b37d9aca156dd9-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 209,
        "output_files": 209,
        "local_pdfs": 209
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Anthology.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Anthology",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Anthology.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 289,
              "errors": 0,
              "error_rate": 0.0
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 209
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 209
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 211
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Anthology",
          "pdf_count": 209,
          "total_songs": 209
        },
        "7_local_pdfs": {
          "count": 209
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 209
        }
      },
      "page_analysis_error_rate": 0.0,
      "local_folder": "Beatles\\Beatles - Anthology"
    },
    {
      "book_id": "v2-fa803f4561ecf584-2",
      "completeness": {
        "exists_count": 11,
        "total_expected": 13,
        "percentage": 84.6
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 14,
        "output_files": 14,
        "local_pdfs": 14
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Beatles/Beatles - Revolver _2_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Beatles",
          "book_name": "Revolver _2_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Beatles/Beatles - Revolver _2_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 45,
              "errors": 25,
              "error_rate": 55.6
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 14
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 14
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 14
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Beatles\\Beatles - Revolver _2_",
          "pdf_count": 14,
          "total_songs": 14
        },
        "7_local_pdfs": {
          "count": 14
        },
        "8_provenance": {
          "exists": true,
          "status": "V2_PROCESSED",
          "actual_songs": 14
        }
      },
      "page_analysis_error_rate": 55.55555555555556,
      "local_folder": "Beatles\\Beatles - Revolver _2_"
    },
    {
      "book_id": "v2-fccf094b5cb74c90-2",
      "completeness": {
        "exists_count": 10,
        "total_expected": 13,
        "percentage": 76.9
      },
      "consistency": {
        "status": "CONSISTENT",
        "verified_songs": 4,
        "output_files": 4,
        "local_pdfs": 4
      },
      "artifacts": {
        "1_source_pdf": {
          "exists": true,
          "uri": "s3://jsmith-input/Bonnie Raitt/Bonnie Raitt - Nick Of Time _PVG Book_.pdf"
        },
        "2_dynamodb": {
          "exists": true,
          "status": "success",
          "artist": "Bonnie Raitt",
          "book_name": "Nick Of Time _PVG Book_",
          "songs_extracted": 9,
          "source_pdf_uri": "s3://jsmith-input/Bonnie Raitt/Bonnie Raitt - Nick Of Time _PVG Book_.pdf"
        },
        "3_s3_artifacts": {
          "toc_discovery.json": {
            "exists": true,
            "summary": {
              "pages": 0
            }
          },
          "toc_parse.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "page_analysis.json": {
            "exists": true,
            "summary": {
              "total_pages": 47,
              "errors": 34,
              "error_rate": 72.3
            }
          },
          "page_mapping.json": {
            "exists": true,
            "summary": {
              "songs": 0
            }
          },
          "verified_songs.json": {
            "exists": true,
            "summary": {
              "songs": 4
            }
          },
          "output_files.json": {
            "exists": true,
            "summary": {
              "files": 4
            }
          }
        },
        "4_s3_output_manifest": {
          "exists": true
        },
        "5_s3_output_pdfs": {
          "count": 7
        },
        "6_local_manifest": {
          "exists": true,
          "folder": "Bonnie Raitt\\Bonnie Raitt - Nick Of Time _PVG Book_",
          "pdf_count": 4,
          "total_songs": 4
        },
        "7_local_pdfs": {
          "count": 4
        },
        "8_provenance": {
          "exists": false
        }
      },
      "page_analysis_error_rate": 72.3404255319149,
      "local_folder": "Bonnie Raitt\\Bonnie Raitt - Nick Of Time _PVG Book_"
    }
  ]
};
