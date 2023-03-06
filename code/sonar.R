library(sonaR)
library(glue)


################################################################################
# Based on the package sonaR by KennethTM (https://github.com/KennethTM/sonaR) #

sonar_data <- function(mat_list, channel, fp, n){
  
  rotate <- function(x){t(apply(x, 2, rev))}
  
  count.occurances <- 0
  
  lapply(mat_list, function(frame){
    sonar_range <- attr(frame, "range")
    
    df <- data.frame(sonar_range[1],sonar_range[2])
    
    dir.create(file.path(file.path(fp,glue(n)), glue("{channel}")))
    write.csv(frame, glue(file.path(fp,glue(n)), "/{channel}/frame_{count.occurances}.csv"))
    write.table(df, glue(file.path(fp,glue(n)), "/{channel}/frame_{count.occurances}.csv"), append = TRUE)
    
    count.occurances <<- count.occurances + 1
    
  })
  
}


################################################################################

#fp <- "C:/PATH/PlonerSee"
#fns <- c("Sonar_2022-08-14_16.12.34.sl2")
args = commandArgs(trailingOnly=TRUE)
mypath=args[1]
print("path to config")
print(mypath)


config <- readIniFile(mypath) # Alternatively: "C:/PATH/Tag5/config.ini"
print(config)
#stopifnot(FALSE)
fp <- config[16, "value"]
fns <- c(config[17, "value"])
fns <- as.list(strsplit(fns, ",")[[1]])

for (fn in fns) {
  print(fn)
  f = paste(fp, fn, sep="/")
  sl <- sonar_read(f)
  
  n = gsub('([.])', '', fn)
  dir.create(file.path(fp,glue(n)))
  
  
  sl_primary <- sonar_image(sl, channel = "Primary")
  
  sonar_data(sl_primary, "Primary", fp, n)
  
  
  #sl_secondary <- sonar_image(sl, channel = "Secondary")
  
  #sonar_data(sl_secondary, "Secondary", fp, n)
  
  
  sl_down <- sonar_image(sl, channel = "Downscan")
  
  sonar_data(sl_down, "Downscan", fp, n)
  
  
  sl_sidescan <- sonar_image(sl, channel = "Sidescan")
  
  sonar_data(sl_sidescan, "Sidescan", fp, n)
  
  
  df <- sl[,c('SurveyTypeLabel','Latitude','Longitude','XLowrance','YLowrance','MinRange','MaxRange','WaterDepth',
              'WaterTemperature','GNSSAltitude','GNSSSpeed','GNSSHeading')]
  
  write.csv(df, glue(fp, "/", {n}, "/sl.csv", sep="/"))
}


