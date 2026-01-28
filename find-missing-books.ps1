# Find the actual paths for missing books

$missingBooks = @(
    @{Artist="America"; Book="America - Greatest Hits [Book] "},
    @{Artist="Ben Folds"; Book="Ben Folds - Rockin' The Suburbs [Book]"},
    @{Artist="Crosby Stills and Nash"; Book="Crosby, Stills, Nash & Young - The Guitar Collection"},
    @{Artist="Dire Straits"; Book="Dire Straits - Mark Knopfler Guitar Styles Vol 1 [Guitar Book]"},
    @{Artist="ELO"; Book="Elton John - The Elton John Collection [Piano Solos]"},
    @{Artist="Elvis Presley"; Book="Elvis Presley - The Compleat [PVG Book]"},
    @{Artist="Kinks"; Book="Kinks - Guitar Legends [Tab]"},
    @{Artist="Mamas and the Papas"; Book="Mamas and The Papas - Songbook [PVG]"},
    @{Artist="Night Ranger"; Book="Night Ranger - Best Of 2 [Jap Score]"},
    @{Artist="Robbie Robertson"; Book="Robbie Robertson - Songbook [Guitar Tab]"},
    @{Artist="Tom Lehrer"; Book="Tom Lehrer - Too Many Songs [PVC Book]"},
    @{Artist="Wings"; Book="Wings - Over America [PVG]"},
    @{Artist="_Broadway Shows"; Book="Various Artists - 25th Annual Putnam County Spelling Bee"},
    @{Artist="_Broadway Shows"; Book="Various Artists - High School Musical 1 [Libretto]"},
    @{Artist="_Broadway Shows"; Book="Various Artists - Little Shop Of Horrors (Broadway)"},
    @{Artist="_Broadway Shows"; Book="Various Artists - You're A Good Man Charlie Brown (Score)"}
)

$found = @()

foreach ($book in $missingBooks) {
    $artistPath = "C:\Work\AWSMusic\SheetMusic\$($book.Artist)"
    
    if (Test-Path $artistPath) {
        # Search for PDFs recursively
        $pdfs = Get-ChildItem $artistPath -Recurse -Filter "*.pdf" | Where-Object {
            $_.Name -like "*$($book.Book.Trim())*" -or
            $_.BaseName -eq $book.Book.Trim() -or
            $_.BaseName -like "$($book.Book.Trim())*"
        }
        
        if ($pdfs) {
            foreach ($pdf in $pdfs) {
                $found += [PSCustomObject]@{
                    Artist = $book.Artist
                    BookName = $book.Book.Trim()
                    ActualPath = $pdf.FullName
                    ActualName = $pdf.Name
                }
                Write-Host "FOUND: $($book.Artist) - $($pdf.Name)" -ForegroundColor Green
            }
        } else {
            Write-Host "NOT FOUND: $($book.Artist) - $($book.Book)" -ForegroundColor Red
        }
    } else {
        Write-Host "ARTIST FOLDER NOT FOUND: $($book.Artist)" -ForegroundColor Red
    }
}

if ($found.Count -gt 0) {
    $found | Export-Csv "found-missing-books.csv" -NoTypeInformation -Encoding UTF8
    Write-Host ""
    Write-Host "Found $($found.Count) books. Saved to found-missing-books.csv" -ForegroundColor Cyan
}
