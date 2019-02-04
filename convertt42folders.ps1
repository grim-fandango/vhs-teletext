
$ErrorActionPreference = "Stop"
#$files = Get-ChildItem -Directory | Where-Object { (Get-ChildItem $_ -Directory -Recurse -Filter t42) -and  -not (Get-ChildItem $_ -File -Recurse -Filter *.t42) } | Select-Object Name, LastWriteTime
$files = Get-ChildItem -Directory | Where-Object { (Get-ChildItem $_ -Directory -Recurse -Filter t42) } | Select-Object Name, LastWriteTime

foreach ($file in $files)
{
	## If the .t42 file already exists then recycle the t42 folder
	Write-Host Testing existence of ( $file.Name + "\" + $file.Name + ".t42" )
	if (Test-Path ( $file.Name + "\" + $file.Name + ".t42" ))
	{
		Write-Host t42 folder already exists, so recycling...
		Remove-ItemSafely ( $file.Name + "\t42" )
		Write-Host Recycled.
	}
	else
	{
		if (Test-Path ( $file.Name + "\t42" ) )
		{
			# Create the .t42 file from the t42 folder
			Write-Host Creating t42 file...
			gc ( $file.Name + "\t42\*" ) -Enc Byte -Read 512 | sc ( $file.Name + "\" + $file.Name + ".t42" ) -Enc Byte
			Write-Host Created.
			
			Write-Host Recycling t42 folder...
			# Recycle the t42 folder
			Remove-ItemSafely ( $file.Name + "\t42" )
			Write-Host Recycled.
		}
		else
		{
			Write-Host t42 folder not found, no changes made.
		}
	}
	
    #$file.Name
    #$file.length
	Write-Host `n
}

#gc ( "_ytv-19900929\t42\*" ) -Enc Byte -Read 512 | sc ( "_ytv-19900929\_ytv-19900929.t42" ) -Enc Byte