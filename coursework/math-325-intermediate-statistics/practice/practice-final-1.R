


#THIS IS MY NOTEBOOK LINK THAT I WILL USE TO OPEN IT IN HTML
#  (see the course Statistics Notebook)



library(mosaic)
View(KidsFeet) 
footlm <- lm(length ~ width, data = KidsFeet)
summary(footlm) 
# find the equation of the lm y - 9.8 + 1.65x


RT <- RailTrail
RT$Season <- as.factor(with(RT, spring + 2*summer + 3*fall))
boxplot(precip ~ Season, data=RT)
# to tell which method is better


View(RailTrail)
RailTrail2 <- filter(RailTrail, summer == "0")
raillm <- lm(volume ~ hightemp, data = RailTrail2)
summary(raillm)
plot(raillm)
plot(volume ~ hightemp, data = RailTrail)
# find the coef for the lm y = -232 + 9.3x


table(KidsFeet$sex)
# how many boy v girls


kidfoot87 <- filter(KidsFeet, birthyear == "87")
kidfoot88 <- filter(KidsFeet, birthyear == "88")
mean(kidfoot87$length)
mean(kidfoot88$length)
# averages for lengths of feet for 2 years


#remember that if u want a prediction of x values from yes or no - log
#The Wilcoxon Rank Sum Test is the only option provided that allows the comparison of two groups of quantitative data. Other appropriate tests would be an Independent Samples t Test or a Permutation Test.


kidfoot.glm <- glm(sex ~ length, data = KidsFeet, family = binomial)
summary(kidfoot.glm)
#probabilty that length of foot is boy e^x   "x = -0.5074"
kids.glm <- glm(sex=="B" ~ width, data=KidsFeet, family=binomial)
predict(kids.glm, data.frame(width=9.5), type="response")
1
0.7306367
plot(sex=="B" ~ width, data=KidsFeet)
b <- coef(kids.glm)
curve(exp(b[1]+b[2]*x)/(1+exp(b[1]+b[2]*x)), add=TRUE)
abline(h=9.5, v=0.73, lty=2)
abline(v=9.5, h=0.73, lty=2)
# correct answer


wilcox.test(KidsFeet$width, mu = 8, alternative = "two.sided")
# wilcox test on feet width being 8 or not


their.glm <- glm( (volume>350) ~ hightemp + weekday, data=RailTrail, family=binomial)
summary(their.glm)
b <- coef(their.glm)
b
plot( ( (volume>350) + as.numeric(as.character(weekday))/100 ) ~ hightemp, data=RailTrail, col=weekday, ylim = c(-1000, 1000), ylab="Probability there are Over 200 Trail Users", xlab="Daily High Temperature")
curve(exp(b[1] + b[2]*x) / (1 + exp(b[1] + b[2]*x)), add = TRUE)
#You need to run appropriate code to add the curves to the plot.


RT <- RailTrail
RT$Season <- as.factor(with(RT, spring + 2*summer + 3*fall))
seezaov <- aov(hightemp ~ weekday * Season, data = RT)
summary(seezaov)
#1. Is average hightemp different on weekends than it is on weekdays?
#   0.0101
#2. Is average hightemp different during any of the three seasons?
#   1.36e-14
#3. Do average hightemp differences between weekends and weekdays differ in magnitude in the various seasons?
#   0.5511

trail.glm <- glm(summer ~ avgtemp, data = RailTrail, family = "binomial")
summary(trail.glm)
# find the p-value of the slope

RT <- RailTrail
RT$Season <- as.factor(with(RT, spring + 2*summer + 3*fall))
kruskal.test(volume ~ Season, data = RT)
# Which season has more people per trail (I think 1 is spring so thats what i formated the answer as)
boxplot(volume ~ Season, data=RT)
#dont forget to check plots of the data


feets.lm <- lm(length ~ width, data = KidsFeet)
summary(feets.lm)
plot(feets.lm)
# find which plot this lm is wrong with
#correct answer was QQPLOT


#Remember to find the slope for the interaction term you need to
#add the slope and the offset together

w <- table(RT$precip, RT$Season)
x <- table(RT$precip, RT$spring)
y <- table(RT$precip, RT$summer)
z <- table(RT$precip, RT$fall)
chisq.test(w)
chisq.test(x)
chisq.test(y)
chisq.test(z)
barplot(w)
barplot(x)
barplot(y)
barplot(z)
# to find the p-value of a graph. couldnt find it tho


asdf <- table(KidsFeet$biggerfoot, KidsFeet$domhand)
fdsa<-chisq.test(asdf)
fdsa
fdsa$expected
#to check if a chi ^2 was valid


pred <- predict(chall.glm, data.frame(temp=31), type='response')
#to check the odds of a specific value
