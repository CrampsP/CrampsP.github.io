library(readr)
library(tidyverse)
library(mosaic)
library(car)
students_scores <- read_csv("~/CSE 111/students_scores.csv")
View(students_scores)

wilcox.test(students_scores$final_score_40pt[students_scores$treatment_group=="Less Homework (-2h)"],students_scores$final_score_40pt[students_scores$treatment_group=="More Homework (+2h)"], mu = 0, paired=TRUE, alternative = "two.sided", conf.leel = 0.95)
boxplot(final_score_40pt ~ treatment_group, students_scores)
favstats(students_scores$final_score_40pt[students_scores$treatment_group=="Less Homework (-2h)"],students_scores$final_score_40pt[students_scores$treatment_group=="More Homework (+2h)"])
students_scores %>% 
  group_by(treatment_group) %>% 
  summarise(favstats(final_score_40pt))


Honda_mpg <- data.frame(date = c("06/01/20", "08/19/20", "09/14/20", "01/07/21", "07/22/21", "08/16/21", "10/24/21", "12/31/21", "03/12/22", "05/04/22", "07/09/22", "10/12/22"), milesDriven = c(274.4, 266.8, 317.0, 113.4, 326.2, 62.6, 239.8, 242.0, 195.6, 106.4, 379.3, 325.4), gallonsUsed = c(12.42, 12.255, 15.224, 7.953, 16.378, 3.285, 13.230, 10.467, 9.310, 4.721, 16.958, 16.221))

View(Honda_mpg)

Honda_mpg <- Honda_mpg %>% 
  mutate(mpg = (milesDriven/gallonsUsed))

ggplot(Honda_mpg, mapping = aes(mpg))+
  geom_dotplot(binwidth = .1) +   
  geom_segment(aes(x=17, xend=17, y=0, yend=0.5), color="skyblue") +
  geom_text(aes(x=17, y=.6), label="Median Hypothesized to be 17 mpg", color="skyblue") + 
  labs(title="2010 Honda Odyssey Gas Mileages", y="", x="Miles Per Gallon Vehicle Achieved on Systematically Selected Dates") + 
  theme(axis.ticks.y=element_blank(), axis.text.y=element_blank())

wilcox.test(Honda_mpg$mpg, mu = 17, alternative = "two.sided")


ggplot(Honda_mpg, aes(x=mpg)) +
  geom_dotplot(binwidth = .1) +
  geom_segment(aes(x=17, xend=17, y=0, yend=0.5), color="skyblue") +
  geom_text(aes(x=17, y=.6), label="Median Hypothesized to be 17 mpg", color="skyblue") +
  labs(title="2010 Honda Odyssey Gas Mileages", y="", x="Miles Per Gallon Vehicle Achieved on Systematically Selected Dates") +
  theme(axis.ticks.y=element_blank(), axis.text.y=element_blank())


Honda_mpg$mpg - 17

View(Duncan)

NewDuncan <- filter(Duncan, type == "wc" | type == "prof")

View(NewDuncan)

# approximate Wilcoxon (normal approximation)
res_approx <- wilcox.test(prestige ~ type,
                          data = NewDuncan,
                          alternative = "greater",
                          exact = FALSE,      # force approximate method
                          correct = TRUE)     # default: continuity correction on
res_approx

boxplot(prestige ~ type, NewDuncan)

favstats(prestige ~ type, data = NewDuncan)


View(Salaries)

Salaries2 <- Salaries %>%
  mutate(rank = as.character(rank))

View(Salaries2)

boxplot(salary ~ sex, Salaries2)

Professors <- Salaries2 %>%
  filter(rank == "Prof")

Prof_summary <- Professors %>%
  group_by(sex) %>%
  summarise(
    Median_Annual_Salary = round(median(salary, na.rm = TRUE)),
    Sample_Size = n()
  )

Prof_summary

wilcox.test(salary ~ sex, 
            data = Professors,
            alternative = "two.sided",
            exact = FALSE)  # use approximate method (ties exist)

View(Davis)

Davis2 <- Davis %>%
  filter(sex == "M") %>%  # reduce to just men
  mutate(weight_diff = weight - repwt)  # compute the difference (actual - reported)

plot(weight_diff, Davis2)

# Wilcoxon Signed-Rank Test for median difference ≠ 0
wilcox.test(Davis2$weight_diff, mu = 0, alternative = "two.sided")

