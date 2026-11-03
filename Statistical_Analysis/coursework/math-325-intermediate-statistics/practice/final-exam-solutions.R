library(car)
library(mosaic)
library(tidyverse)
YoungAdults <- read_csv("https://raw.githubusercontent.com/saundersg/Statistics-Notebook/master/Data/YoungAdults.csv")
View(YoungAdults)

#Question 1
YA <- lm(Weight ~ Height, data = YoungAdults)
summary(YA)
predict(YA, data.frame(Height = 183))


#Question 5
kruskal.test(Religiosity_score ~ Lying, data = YoungAdults)
boxplot(Religiosity_score ~ Lying2, data = YoungAdults2)
YoungAdults2 <- YoungAdults %>% 
  mutate(
    Lying2 = case_when(
      Lying == "never" ~ "A",
      Lying == "only to avoid hurting someone" ~ "B",
      Lying == "sometimes" ~ "C",
      Lying == "everytime it suits me" ~ "D"
    )
  )
View(YoungAdults2)

#Question 6
wilcox.test(Religiosity_score ~ Dominant_hand, data = YoungAdults)

YoungAdults3 <- filter(YoungAdults, Number_of_siblings == "0" & Smoking == "never smoked" & Lying == "never")
View(YoungAdults3)

YoungAdults4 <- YoungAdults %>% 
  mutate(BMI = YoungAdults$Weight/(YoungAdults$Height/100)^2)
View(YoungAdults4)
boxplot(BMI ~ Gender, data = YoungAdults4)


t.test(Fear_score ~ Only_child, data = YoungAdults)


YAov <- aov(Religiosity_score ~ Alcohol, data = YoungAdults)
summary(YAov)
favstats(Religiosity_score ~ Alcohol, data = YoungAdults)
YoungAdults5 <- YoungAdults %>% 
  mutate(
    Only_Child2 = case_when(
      Only_child == "no" ~ "0",
      Only_child == "yes" ~ "1"))
View(YoungAdults5)
lyinglm <- glm(as.numeric(Only_Child2) ~ Number_of_siblings, data = YoungAdults5)
summary(lyinglm)
b <- coef(lyinglm)
b


x <- table(YoungAdults$Punctuality, YoungAdults$Lying)
x
chisq.test(x)
barplot(x, beside = TRUE)



YA2 <- YoungAdults %>% 
  select(I_like_music, Music_diversity_score) %>% 
  filter(I_like_music %in% c("Agree", "Disagree", "Neutral", "Strongly Agree", "Strongly Disagree")) %>% 
  mutate(I_like_music = factor(I_like_music, levels = c("Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"), ordered = TRUE)) %>% 
  na.omit()
View(YA2)


YoungAdults.hwg <- YoungAdults %>% 
  select(Height, Weight, Gender) %>% 
  na.omit()
View(YoungAdults.hwg)
ggplot(YoungAdults.hwg, aes(x = Height, y = Weight, color = Gender))+
  geom_point() + 
  geom_smooth(methon = "lm", se = F)
hwglm <- lm(Weight ~ Height * Gender, data = YoungAdults.hwg)
summary(hwglm)
b <- coef(hwglm)
b
plot(Weight ~ Height * Gender, data = YoungAdults.hwg, xlim = c(125, 225))
curve(b[1] + b[2]*x, col = "grey", add = TRUE)
curve((b[1]+b[3]) + (b[2]+b[4])*x, col = "skyblue", add = TRUE)


YoungAdults3 <- filter(YoungAdults, Smoking == "never smoked" & Smoking == "never smoked" & Lying == "never")
View(YoungAdults3)





# First run the initial test and gain the test statistic:
myTest <- t.test(extra ~ group, data = sleep, mu = 0)
observedTestStat <- myTest$statistic
# Now we run the permutations to create a distribution of test statistics
N <- 2000
permutedTestStats <- rep(NA, N)
for (i in 1:N){
  permutedTest <- t.test(sample(extra) ~ group, data = sleep, mu = 0)
  permutedTestStats[i] <- permutedTest$statistic
}
# Now we show a histogram of that distribution
hist(permutedTestStats, col = "skyblue")
abline(v = observedTestStat, col = "red", lwd = 3)
#Greater-Than p-value: Not the correct one in this case
sum(permutedTestStats >= observedTestStat)/N
# Less-Than p-value: Not the correct one for this data
sum(permutedTestStats <= observedTestStat)/N
# Two-Sided p-value: This is the one we want based on our alternative hypothesis.
2*sum(permutedTestStats <= observedTestStat)/N



t.test(Happiness_score ~ Gender, data = YoungAdults)



last <- aov(Weight ~ Gender * I_live_a_healthy_lifestyle, data = YoungAdults)
summary(last)
xyplot(Weight ~ as.factor(I_live_a_healthy_lifestyle), data = YoungAdults)


YA6 <- filter(YoungAdults, I_live_a_healthy_lifestyle == "Agree" & Gender == "male")
mean(YA6$Weight, na.rm = TRUE)

kruskal.test(Music_diversity_score ~ Education, data = YoungAdults)



YoungAdults %>% 
  filter(I_like_music != "#N/A", !is.na(Gender), !is.na(Punctuality)) %>% 
  mutate(I_like_music = factor(I_like_music, levels = c("Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"), ordered = TRUE)) %>% 
  ggplot(aes(x=I_like_music, y = Happiness_score)) + 
  geom_boxplot() + 
  facet_wrap(~Punctuality) +
  coord_flip()
