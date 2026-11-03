# 2-sample independent t-test
Ho : mu1 = mu2    /\ mu1-mu2 = 0  #no difference in population averages
Ha : mu1 =! mu2
#permutation basically changes the categorical part of the data


# 2-sample paired t-test
Ho : mu of differences = 0 #no difference between deviation
Ha : mu of differences =! 0

# ANOVA
Ho : mu1 = mu2 = mu3.... #no difference between averages
Ha : At least one mu is different
#permutation basically changes the categorical part of the data


# Simple Linear Regression
Ho : B1 = 0   #no relationship between x and y
Ha : B1 =! 0
#permutation randomly switches the values of y


# Log Regression
Ho : B1 = 0 #no relationship between x and y
Ha : B1 =! 0
#permutation randomly switches the values of y



#QUESTION 1
View(mtcars)
mycars <- filter(mtcars, cyl %in% c(4,8))
View(mycars)
#Step 1
myTest <- t.test(wt ~ cyl, data = mycars, mu = 0)
observedTestStat <- myTest$statistic

#Step 2
N <- 2000      
permutedTestStats <- rep(NA, N)
for (i in  1:N){
  permutedTest <- t.test(sample(wt) ~ cyl, data = mycars, mu = 0)
  permutedTestStats[i] <- permutedTest$statistic
}
hist(permutedTestStats, xlim = c(-9,9))
abline(v=observedTestStat)

#Step 3
sum(permutedTestStats >= observedTestStat)/N
sum(permutedTestStats <= observedTestStat)/N





library(mosaic)
library(tidyverse)

View(diamonds)
#QUESTION 2
#Step 1
myTest <- aov(price ~ clarity, data = diamonds)
observedTestStat <- summary(myTest)[[1]]$`F value`[1]

#Step 2
N <- 100      
permutedTestStats <- rep(NA, N)
for (i in  1:N){
  permutedTest <- aov(sample(price) ~ clarity, data = diamonds)
  permutedTestStats[i] <- summary(permutedTest)[[1]]$`F value`[1]
}
hist(permutedTestStats)
abline(v=observedTestStat)

#Step 3
sum(permutedTestStats >= observedTestStat)/N
sum(permutedTestStats <= observedTestStat)/N





View(SAT)
#Step 1
myTest <- glm((sat> 1000) ~ expend, data = SAT, family = binomial)
observedTestStat <- summary(myTest)[[12]][2,3]

#Step 2
N <- 100      
permutedTestStats <- rep(NA, N)
for (i in  1:N){
  permutedTest <- glm(sample((sat> 1000)) ~ expend, data = SAT, family = binomial)
  permutedTestStats[i] <- summary(permutedTest)[[12]][2,3]
}
hist(permutedTestStats)
abline(v=observedTestStat)

#Step 3
sum(permutedTestStats >= observedTestStat)/N
sum(permutedTestStats <= observedTestStat)/N




set.seed(1140411) #allows us each to get the same set of random values
sample1 <- rnorm(30, 69, 2.5) #get a random sample of n=30 normally distributed values with mu=69 and sigma=2.5
sample2 <- rnorm(30, 69, 2.5) #get another random sample of n=30 normally distributed values with mu=69 and sigma=2.5
theData <- data.frame(values = c(sample1,sample2), group = rep(c(1,2), each=30)) #load the random samples into a data set
View(theData)
boxplot(values ~ group, data = theData)

set.seed(1140411)
sample1 <- rnorm(30, 69, 2.5)
sample2 <- rnorm(30, 69, 2.5)
theData <- data.frame(values = c(sample1,sample2), group = rep(c(1,2), each=30))
View(theData)
boxplot(values ~ group, data = theData)
myTest <-  t.test(values ~ group, data = theData, mu = 0)
observedTestStat <- myTest$statistic
observedTestStat
N <- 2000      
permutedTestStats <-  rep(NA, N)
for  (i in 1:N ) {
  permutedTest <- t.test(sample(values) ~ group, data = theData, mu = 0)
  permutedTestStats[i]  <-  permutedTest$statistic
}
hist(permutedTestStats)
abline(v=observedTestStat)
sum(permutedTestStats >= observedTestStat)/N
sum(permutedTestStats <= observedTestStat)/N
2*sum(permutedTestStats <= observedTestStat)/N







set.seed(121) #ensure we each get the same set of random values
sample1 <- rnorm(30, 185, 8) #randomly sample n=30 normally distributed values with a mu=185 and sigma=8.
sample2 <- sample1 - rnorm(30, 0, 3.5) #randomly shift each value from sample1, but with mu=0 change overall.
theData <- data.frame(values = c(sample1,sample2), group = rep(c(1,2), each=30), id = rep(c(1:30),times=2)) #load the data into a data set
View(theData)
with(theData, hist(values[group==1] - values[group==2]))

set.seed(121)
sample1 <- rnorm(30, 185, 8)
sample2 <- sample1 - rnorm(30, 0, 3.5)
theData <- data.frame(values = c(sample1,sample2), group = rep(c(1,2), each=30), id = rep(c(1:30),times=2))
View(theData)
with(theData, hist(values[group==1] - values[group==2]))
myTest <- t.test(theData$values[theData$group == 1],theData$values[theData$group == 2], paired = TRUE, mu = 0)
observedTestStat <- myTest$statistic
observedTestStat
N <- 2000      
permutedTestStats <-  rep(NA, N)
for  (i in 1:N ) {
  permutedData <- sample(x=c(1,-1), size=30, replace=TRUE)
  permutedTest <- with(theData, t.test(permutedData*(values[group==1] - values[group==2]), mu = 0))
  permutedTestStats[i]  <-  permutedTest$statistic
}
hist(permutedTestStats)
abline(v=observedTestStat)
sum(permutedTestStats >= observedTestStat)/N
sum(permutedTestStats <= observedTestStat)/N
2*sum(permutedTestStats <= observedTestStat)/N
