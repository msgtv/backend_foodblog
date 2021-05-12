import sqlite3
import argparse


class FoodBlogBackend:
    data = {"meals": ("breakfast", "brunch", "lunch", "supper"),
            "ingredients": ("milk", "cacao", "strawberry", "blueberry", "blackberry", "sugar"),
            "measures": ("ml", "g", "l", "cup", "tbsp", "tsp", "dsp", "")}
    recipe_name = None
    recipe_description = None
    recipe_id = None
    parser = argparse.ArgumentParser(description="It is a food blog management database.")
    parser.add_argument('database', help='Database name')
    parser.add_argument('--ingredients', help='Ingredients list')
    parser.add_argument('--meals', help='Meals list')
    args = parser.parse_args()
    conn = sqlite3.connect(args.database)
    cur = conn.cursor()

    def __init__(self):
        self.create_tables()

    def create_tables(self):
        # Create tables 'meals', 'ingredients', 'measures'
        for key in self.data.keys():
            self.cur.execute(f"CREATE TABLE IF NOT EXISTS {key}("
                             f"   {key[:-1]}_id INTEGER PRIMARY KEY,"
                             f"   {key[:-1]}_name TEXT {'NOT NULL' if key != 'measures' else ''} UNIQUE);")

            for value in self.data[key]:
                self.cur.execute(f"INSERT INTO {key} ({key[:-1]}_name)"
                                 f"SELECT '{value}'"
                                 "WHERE NOT EXISTS"
                                 f"     (SELECT 1 FROM {key} WHERE {key[:-1]}_name = '{value}');")

        # Create the 'recipes' table
        self.cur.execute("CREATE TABLE IF NOT EXISTS recipes("
                         "  recipe_id INTEGER PRIMARY KEY,"
                         "  recipe_name TEXT NOT NULL,"
                         "  recipe_description TEXT);")

        # Create a 'serve' table
        self.cur.execute("CREATE TABLE IF NOT EXISTS serve("
                         "  serve_id INTEGER PRIMARY KEY,"
                         "  meal_id INTEGER NOT NULL,"
                         "  recipe_id INTEGER NOT NULL,"
                         "  FOREIGN KEY (meal_id)"
                         "      REFERENCES meals (meal_id),"
                         "  FOREIGN KEY (recipe_id)"
                         "      REFERENCES recipes (recipe_id));")

        # Create a 'quantity' table
        self.cur.execute("CREATE TABLE IF NOT EXISTS quantity("
                         "  quantity_id INTEGER PRIMARY KEY,"
                         "  quantity INTEGER NOT NULL,"
                         "  recipe_id INTEGER NOT NULL,"
                         "  measure_id INTEGER NOT NULL,"
                         "  ingredient_id INTEGER NOT NULL,"
                         "  FOREIGN KEY (recipe_id)"
                         "      REFERENCES recipes (recipe_id),"
                         "  FOREIGN KEY (measure_id)"
                         "      REFERENCES recipes (measure_id),"
                         "  FOREIGN KEY (ingredient_id)"
                         "      REFERENCES ingredients (ingredient_id));")

        self.conn.commit()

    def get_recipe_id(self):
        if self.recipe_name:
            recipe_id = self.cur.execute(f'SELECT recipe_id '
                                         f'FROM recipes '
                                         f'WHERE recipe_name = "{self.recipe_name}" AND'
                                         f'      recipe_description = "{self.recipe_description}";').fetchall()[-1][-1]
            return recipe_id
        else:
            return None

    def record_recipe(self):
        self.cur.execute("INSERT INTO "
                         "      recipes (recipe_name, recipe_description)"
                         "VALUES"
                         f"     ('{self.recipe_name}', '{self.recipe_description}')")
        self.conn.commit()

    def record_serve(self):
        self.output_meals()
        choice_meal = []
        while len(choice_meal) == 0:
            choice_meal = [int(num) for num in input("When the dish can be served: ").split()]
        for meal_id in choice_meal:
            self.cur.execute("INSERT INTO "
                             "     serve (meal_id, recipe_id)"
                             "VALUES "
                             f"     ({meal_id}, {self.recipe_id});")
        self.conn.commit()

    def output_meals(self):
        meal_name = self.cur.execute("SELECT * FROM meals;")
        print(') '.join(str(x) for x in meal_name.fetchone()), end=' ')
        print(') '.join(str(x) for x in meal_name.fetchone()), end=' ')
        print(') '.join(str(x) for x in meal_name.fetchone()), end=' ')
        print(') '.join(str(x) for x in meal_name.fetchone()))

    def select_id(self, table_name, key):
        query = self.cur.execute(f"SELECT "
                                 f"     {table_name[:-1]}_id "
                                 f"FROM "
                                 f"     {table_name} "
                                 f"WHERE "
                                 f"     {table_name[:-1]}_name LIKE '%{key}%'").fetchall()
        return query

    def record_quantity(self, input_quantity):
        if 2 <= len(input_quantity) <= 3:
            quantity = input_quantity[0]
            measure = input_quantity[1] if len(input_quantity) == 3 else ''
            ingredient = input_quantity[2] if len(input_quantity) == 3 else input_quantity[1]
            if measure and len(self.select_id('measures', measure)) != 1:
                print("The measure is not conclusive!")
            elif len(self.select_id('ingredients', ingredient)) != 1:
                print("The ingredient is not conclusive!")
            else:
                measure = self.select_id('measures', measure)[0][0]
                ingredient = self.select_id('ingredients', ingredient)[0][0]
                self.cur.execute("INSERT INTO "
                                 "     quantity (quantity, recipe_id, measure_id, ingredient_id) "
                                 "VALUES "
                                 f"     ({quantity}, {self.recipe_id}, {measure}, {ingredient});")
                self.conn.commit()

    def add_recipe(self):
        while True:
            self.recipe_name = input("Recipe name: ")
            if self.recipe_name:
                self.recipe_description = input("Recipe description: ")
                self.record_recipe()
                self.recipe_id = self.get_recipe_id()
                self.record_serve()

                # QUANTITY
                while True:
                    input_quantity = input("Input quantity of ingredient <press enter to stop>:").split()  # quantity measure ingredient
                    if input_quantity:
                        self.record_quantity(input_quantity)
                    else:
                        break

            else:
                self.conn.close()
                break

    def output_recipe_name(self):
        ingredients = set(self.args.ingredients.strip("'").split(',')) if self.args.ingredients else []
        meals = set(self.args.meals.strip("'").split(',')) if self.args.meals else []
        main_query = "SELECT recipe_name FROM recipes WHERE "
        query_ingredients = ['recipe_id IN ('
                             'SELECT recipe_id '
                             'FROM quantity '
                             'WHERE ingredient_id IN ('
                                    'SELECT ingredient_id '
                                    'FROM ingredients '
                                    f'WHERE ingredient_name LIKE "{name}"))' for name in ingredients]
        query_meals = ['recipe_id IN ('
                       'SELECT recipe_id '
                       'FROM serve '
                       'WHERE meal_id IN ('
                             'SELECT meal_id '
                             'FROM meals '
                             f'WHERE meal_name="{meal}"))' for meal in meals]
        query_ingredients = '(' + ' AND '.join(query_ingredients) + ')'
        query_meals = '(' + ' OR '.join(query_meals) + ')'
        if meals and ingredients:
            main_query += query_ingredients + ' AND ' + query_meals + ';'
        elif not meals and ingredients:
            main_query += query_ingredients + ';'
        elif not ingredients and meals:
            main_query += query_meals + ';'
        answer = self.cur.execute(main_query).fetchall()
        answer = ', '.join([''.join(name) for name in answer])
        if answer:
            print(f'Recipes selected for you: {answer}')
        else:
            print("There are no such recipes in the database.")
        self.conn.close()

    def main(self):
        if self.args.ingredients or self.args.meals:
            self.output_recipe_name()
        else:
            self.add_recipe()


blog = FoodBlogBackend()
blog.main()
