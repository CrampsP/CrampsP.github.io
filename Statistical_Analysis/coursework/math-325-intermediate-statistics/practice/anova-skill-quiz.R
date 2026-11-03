library(car) 
friendly.aov <- aov(correct ~ condition, data=Friendly)
summary(friendly.aov)
par(mfrow=c(1,2))
plot(friendly.aov, which=1:2)


data(ToothGrowth)

ToothGrowth$dose <- as.factor(ToothGrowth$dose)
ToothGrowth$supp <- as.factor(ToothGrowth$supp)

anova_result <- aov(len ~ supp * dose, data = ToothGrowth)
summary(anova_result)

plot(anova_result)


library(lattice)
xyplot(len ~ supp, data=ToothGrowth, type=c("p","a"),
       main="Orange Juice Showing Longer Teeth on Average in Guinea Pigs",
       ylab="Length of Odontoblasts", xlab="Vitamin C Delivery Method")

aggregate(len ~ supp, ToothGrowth, mean)

xyplot(len ~ dose, data=ToothGrowth, type=c("p","a"),
       main="Higher Doses Showing Longer Teeth on Average in Guinea Pigs",
       ylab="Length of Odontoblasts", xlab="Dosage Level in mg/day")
