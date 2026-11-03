library(mosaic)
View(KidsFeet)
wilcox.test(width ~ sex, data = KidsFeet, mu = 0, alternative = "two.sided")
# wilcox test on finding p-value of median


#in finding permutated test p-values add all the tail values and / by amount of test statistics


Util <- Utilities
View(Util)
Util$Season <- cut(Util$month%%12, c(0,2,5,8,11), c("Winter","Spring","Summer","Fall"))
boxplot(elecbill ~ Season, data=Util, main="A Residence in Minnesota", ylab="Monthly Electricity Bill (US Dollars)", xlab="Season of the Year", col=c("skyblue","darkseagreen3","coral","goldenrod"))
kruskal.test(elecbill ~ Season, data = Util)
# find if the seasons r stochastically different


util.lm <- lm(gasbill ~ temp + I(temp^2), data=Utilities)
plot(gasbill ~ temp, data=Utilities)
b <- util.lm$coefficients
curve(b[1] + b[2]*x + b[3]*x^2, add=TRUE)
summary(util.lm)
#find the equation based off the information


U2 <- subset(Utilities, month %in% c(3,6))
View(U2)
plot(gasbill ~ elecbill, data=U2, col=month)
ultlm <- lm(gasbill ~ elecbill * month, data=U2)
summary(ultlm)
#correct answer is p-value of interaction term
b <- coef(ultlm)
b
curve(b[1] + b[2]*x, col="skyblue", lwd=2, add=TRUE)  #baseline (in blue)
curve((b[1] + b[3]) + (b[2] + b[4])*x, col="orange", lwd=2, add=TRUE) #changed line (in orange)
# find the p value of the lines of this linear regression using the plot


July <- filter(Utilities, month == 7)
july <- lm(elecbill ~ month, data = Utilities)
july
summary(july)
b <- coef(july)
b
plot(elecbill ~ month, data = Utilities)
curve(b[1] + b[2]*x, col="skyblue", lwd=2, add=TRUE)  #baseline (in blue)
predict(july, data.frame(month = 7))
#predict the value w lm


barplot(KidsFeet$length)
View(KidsFeet)



watt <- lm(elecbill ~ kwh, data = Utilities)
watt
summary(watt)
#correct answer is coef of slope
b <- coef(watt)
b

# remember that odds are calculated by taking the coef and doing e^x


# e^(-x^2)/2!!!!!!!!!!! for finding p value


year <- glm(birthyear=="88" ~ length, data = KidsFeet, family = "binomial")
year
summary(year)
b <- coef(year)
b
plot(birthyear ~ length, data = KidsFeet)
curve(b[1] + b[2]*x, col="skyblue", lwd=2, add=TRUE)  #baseline (in blue)
predict(year, data.frame(length = 26), type="response")
#predict the odds w glm


kiddies <- lm(width ~ birthmonth, data = KidsFeet)
summary(kiddies)
# find p-value of slope


plot(length ~ domhand, data = KidsFeet)
#match the plot

x <- table(KidsFeet$sex, KidsFeet$birthmonth)
barplot(x, beside=TRUE)
#match the plot


kidfootJan <- filter(KidsFeet, birthmonth == "1")
mean(kidfootJan$length)


